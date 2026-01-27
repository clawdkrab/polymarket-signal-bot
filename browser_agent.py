#!/usr/bin/env python3
"""
BROWSER-BASED TRADING AGENT
Uses Playwright to actually interact with Polymarket website
For 15-minute BTC Up/Down markets
"""
import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


class BrowserTradingAgent:
    """Live trading via browser automation."""
    
    def __init__(self, config_path: str = "live_config.json", headless: bool = False):
        # Load config
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.capital = self.config["capital"]
        self.initial_capital = self.capital
        self.headless = headless
        
        # Initialize components
        self.price_feed = BTCPriceFeed()
        self.risk_manager = RiskManager(initial_capital=self.capital)
        
        # Override with stricter live settings
        self.risk_manager.max_position_pct = self.config["risk_settings"]["max_position_pct"]
        self.risk_manager.base_position_pct = self.config["risk_settings"]["base_position_pct"]
        
        # State
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Browser
        self.playwright = None
        self.browser = None
        self.page = None
        
        print("="*70)
        print("⚠️  BROWSER TRADING MODE - REAL CAPITAL")
        print("="*70)
        print(f"Capital: ${self.capital:.2f}")
        print(f"Max Position: {self.config['risk_settings']['max_position_pct']*100:.0f}%")
        print(f"Min Confidence: {self.config['risk_settings']['min_confidence']}%")
        print(f"Headless: {self.headless}")
        print("="*70)
        print()
        print("🌐 BROWSER AUTOMATION ACTIVE")
        print("⚠️  WILL INTERACT WITH POLYMARKET.COM")
        print("⚠️  CAPITAL PRESERVATION IS PRIORITY #1")
        print()
        print("="*70)
        print()
    
    def start_browser(self):
        """Launch browser."""
        print("🚀 Starting browser...")
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            
            # Set reasonable viewport
            self.page.set_viewport_size({"width": 1280, "height": 720})
            
            print("✅ Browser started")
            
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            print("   Run: pip install playwright && playwright install chromium")
            sys.exit(1)
    
    def stop_browser(self):
        """Close browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser closed")
    
    def navigate_to_markets(self):
        """Navigate to BTC markets page."""
        print("🧭 Navigating to Polymarket...")
        
        try:
            self.page.goto("https://polymarket.com/markets/crypto", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)  # Let page fully load
            
            print("✅ At crypto markets page")
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def find_15min_markets(self):
        """Find active 15-minute BTC markets on page."""
        print("🔍 Scanning for 15-minute markets...")
        
        try:
            # Get page text
            content = self.page.content()
            text = self.page.inner_text('body')
            
            # Look for "Bitcoin Up or Down" markets
            markets = []
            
            # Try to find market cards/links
            links = self.page.query_selector_all('a[href*="btc"]')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().lower()
                    
                    # Check if it's an up/down market
                    if 'up' in text or 'down' in text or 'updown' in href:
                        markets.append({
                            'url': f"https://polymarket.com{href}" if href.startswith('/') else href,
                            'text': text[:100]
                        })
                except:
                    pass
            
            print(f"{'✅' if markets else '⚠️ '} Found {len(markets)} potential 15-min markets")
            
            for m in markets[:5]:
                print(f"   - {m['text'][:80]}")
            
            return markets
            
        except Exception as e:
            print(f"❌ Error scanning: {e}")
            return []
    
    def get_market_data(self, market_url: str):
        """Navigate to market and extract trading data."""
        print(f"\n📊 Analyzing market: {market_url}")
        
        try:
            self.page.goto(market_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            
            # Extract market data
            text = self.page.inner_text('body')
            
            data = {
                'url': market_url,
                'text_sample': text[:500]
            }
            
            # Try to find YES/NO prices
            # This will need adjustment based on actual Polymarket DOM
            try:
                # Look for price elements (adjust selectors as needed)
                yes_price_el = self.page.query_selector('text=/Yes|UP/')
                no_price_el = self.page.query_selector('text=/No|DOWN/')
                
                # Extract odds
                # NOTE: These selectors are placeholder - need to inspect actual page
                
            except:
                pass
            
            print(f"✅ Market data extracted")
            return data
            
        except Exception as e:
            print(f"❌ Error getting market data: {e}")
            return None
    
    def analyze_signal(self):
        """Get BTC technical analysis signal."""
        print("📈 Analyzing BTC price action...")
        
        # Get price data
        hourly_prices = self.price_feed.get_recent_prices(minutes=240)
        
        if not hourly_prices or len(hourly_prices) < 20:
            print("⚠️  Insufficient price data")
            return None
        
        # Interpolate to 15-min
        prices_15m = self.price_feed.estimate_15min_prices(hourly_prices)
        
        # Technical analysis
        analysis = analyze_price_action(prices_15m)
        
        signal = analysis["signal"]
        confidence = analysis["confidence"]
        
        print(f"   Signal: {signal} | Confidence: {confidence}%")
        print(f"   RSI: {analysis['rsi']:.1f} | Momentum: {analysis['momentum']:+.2f}%")
        
        # Check confidence threshold
        min_conf = self.config["risk_settings"]["min_confidence"]
        if confidence < min_conf:
            print(f"   ⏸️  Confidence too low ({confidence}% < {min_conf}%)")
            return None
        
        # Risk check
        should_trade, risk_reason = self.risk_manager.should_trade(
            capital=self.capital,
            confidence=confidence,
            trades_today=self.trades_today
        )
        
        if not should_trade:
            print(f"   ⏸️  Risk check failed: {risk_reason}")
            return None
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            capital=self.capital,
            confidence=confidence
        )
        
        return {
            'action': signal,
            'confidence': confidence,
            'size': position_size,
            'analysis': analysis
        }
    
    def execute_trade_manual(self, market_url: str, signal: dict):
        """
        Navigate to market and PAUSE for manual execution.
        (Actual automated trading requires wallet connection/signing)
        """
        print(f"\n{'='*70}")
        print(f"🚨 TRADE SIGNAL GENERATED")
        print(f"{'='*70}")
        print(f"Direction: {signal['action']}")
        print(f"Confidence: {signal['confidence']}%")
        print(f"Suggested Size: ${signal['size']:.2f}")
        print(f"Market: {market_url}")
        print(f"{'='*70}\n")
        
        # Navigate to the market
        try:
            self.page.goto(market_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            
            print("✅ Market loaded in browser")
            print("\n⏸️  PAUSED FOR MANUAL EXECUTION")
            print(f"   → Trade: {signal['action']} for ${signal['size']:.2f}")
            print("   → Execute manually, then press ENTER to continue...")
            
            input()  # Wait for user to execute
            
            print("✅ Continuing...")
            
            # Log the trade
            trade_log = Path(__file__).parent / "src" / "memory" / "browser_trades.jsonl"
            trade_log.parent.mkdir(parents=True, exist_ok=True)
            
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "market_url": market_url,
                "action": signal["action"],
                "size": signal["size"],
                "confidence": signal["confidence"],
                "capital_before": self.capital,
                "executed": "manual"
            }
            
            with open(trade_log, 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
            
            self.trades_today += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def run_cycle(self):
        """Run one trading cycle."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting cycle...")
        print(f"Capital: ${self.capital:.2f} | Trades: {self.trades_today}")
        print()
        
        # Navigate to markets
        if not self.navigate_to_markets():
            return
        
        # Find 15-min markets
        markets = self.find_15min_markets()
        
        if not markets:
            print("⚠️  No 15-minute markets found")
            return
        
        # Take the first active market
        market = markets[0]
        print(f"\n🎯 Targeting: {market['text'][:80]}")
        
        # Get trading signal
        signal = self.analyze_signal()
        
        if not signal:
            print("   ⏸️  No trade signal generated")
            return
        
        # Execute (manual for now)
        self.execute_trade_manual(market['url'], signal)
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously."""
        print(f"🤖 BROWSER MODE ACTIVATED")
        print(f"⏱️  Checking every {check_interval} seconds")
        print(f"🛑 Press Ctrl+C to stop")
        print()
        
        self.start_browser()
        
        try:
            while True:
                self.run_cycle()
                print(f"\n💤 Next check in {check_interval}s...")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Trading stopped by user")
            print(f"Final Capital: ${self.capital:.2f}")
            print(f"Trades Today: {self.trades_today}")
        
        finally:
            self.stop_browser()


def main():
    """Main entry point."""
    print()
    print("⚠️" * 35)
    print()
    print("     BROWSER TRADING MODE - 15-MIN BTC MARKETS")
    print()
    print("⚠️" * 35)
    print()
    
    # Check for playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed!")
        print()
        print("Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print()
        return
    
    # Start agent
    agent = BrowserTradingAgent(config_path="live_config.json", headless=False)
    agent.run_continuous(check_interval=60)


if __name__ == "__main__":
    main()
