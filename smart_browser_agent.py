#!/usr/bin/env python3
"""
SMART BROWSER TRADING AGENT
Opens browser ONLY when there's a trade signal (memory efficient)
"""
import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


class SmartTradingAgent:
    """Memory-efficient browser trading - only opens when needed."""
    
    def __init__(self, config_path: str = "live_config.json"):
        # Load config
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.capital = self.config["capital"]
        self.initial_capital = self.capital
        
        # Initialize components (lightweight - no browser yet)
        self.price_feed = BTCPriceFeed()
        self.risk_manager = RiskManager(initial_capital=self.capital)
        
        # Override with stricter live settings
        self.risk_manager.max_position_pct = self.config["risk_settings"]["max_position_pct"]
        self.risk_manager.base_position_pct = self.config["risk_settings"]["base_position_pct"]
        
        # State
        self.trades_today = 0
        
        print("="*70)
        print("🤖 SMART BROWSER MODE - Memory Efficient")
        print("="*70)
        print(f"Capital: ${self.capital:.2f}")
        print(f"Min Confidence: {self.config['risk_settings']['min_confidence']}%")
        print()
        print("⚡ Strategy: Analyze first, open browser only when trading")
        print("💾 Saves memory by not keeping browser open 24/7")
        print()
        print("="*70)
        print()
    
    def analyze_signal(self):
        """Lightweight analysis - no browser needed."""
        print("📈 Analyzing BTC price action...")
        
        # Get price data (lightweight API call)
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
    
    def execute_trade_browser(self, signal: dict):
        """
        Open browser ONLY when we have a trade signal.
        Execute trade, then close browser immediately.
        """
        from playwright.sync_api import sync_playwright
        
        print(f"\n{'='*70}")
        print(f"🚨 TRADE SIGNAL DETECTED - OPENING BROWSER")
        print(f"{'='*70}")
        print(f"Direction: {signal['action']}")
        print(f"Confidence: {signal['confidence']}%")
        print(f"Size: ${signal['size']:.2f}")
        print(f"{'='*70}\n")
        
        playwright = None
        context = None
        
        try:
            print("🚀 Launching browser...")
            playwright = sync_playwright().start()
            
            # Launch with persistent context
            user_data_dir = Path.home() / ".polymarket_browser_data"
            user_data_dir.mkdir(exist_ok=True)
            
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
                viewport={"width": 1280, "height": 720}
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            print("✅ Browser opened")
            print("🧭 Navigating to Polymarket...")
            
            # Navigate to Polymarket crypto markets
            page.goto("https://polymarket.com/markets/crypto", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Find BTC 15-min markets
            print("🔍 Finding 15-minute BTC markets...")
            
            links = page.query_selector_all('a')
            markets = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().lower()
                    
                    if href and ('btc' in href or 'bitcoin' in text):
                        if 'up' in text or 'down' in text or 'updown' in href:
                            full_url = f"https://polymarket.com{href}" if href.startswith('/') else href
                            markets.append({
                                'url': full_url,
                                'text': text.strip()[:100]
                            })
                except:
                    pass
            
            # Deduplicate
            seen = set()
            unique_markets = []
            for m in markets:
                if m['url'] not in seen:
                    seen.add(m['url'])
                    unique_markets.append(m)
            
            if not unique_markets:
                print("⚠️  No markets found - closing browser")
                return False
            
            print(f"✅ Found {len(unique_markets)} markets")
            
            # Take first market
            market = unique_markets[0]
            print(f"🎯 Targeting: {market['text'][:80]}")
            
            # Navigate to market
            page.goto(market['url'], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Here you would execute the trade
            # For now, just show what would happen
            print(f"\n🎯 WOULD EXECUTE:")
            print(f"   Direction: {signal['action']}")
            print(f"   Size: ${signal['size']:.2f}")
            print(f"   Market: {market['text'][:60]}")
            print()
            print("⚠️  Actual execution code commented out for safety")
            print("   Uncomment when ready to trade live")
            
            # Log the signal
            log_file = Path(__file__).parent / "src" / "memory" / "auto_trades.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "market_url": market['url'],
                "market_text": market['text'],
                "action": signal["action"],
                "size": signal["size"],
                "confidence": signal["confidence"],
                "capital_before": self.capital,
                "executed": False,  # Set to True when actually trading
                "note": "Signal detected but execution disabled for safety"
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
            
            print("✅ Signal logged")
            
            return True
            
        except Exception as e:
            print(f"❌ Browser execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # ALWAYS close browser to free memory
            if context:
                print("🛑 Closing browser...")
                context.close()
            if playwright:
                playwright.stop()
            print("✅ Browser closed - memory freed")
    
    def run_cycle(self):
        """Run one cycle: analyze, then trade if signal exists."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting cycle...")
        print(f"Capital: ${self.capital:.2f} | Trades Today: {self.trades_today}")
        print()
        
        # Step 1: Lightweight analysis (no browser)
        signal = self.analyze_signal()
        
        if not signal:
            print("   ⏸️  No trade signal - staying lightweight")
            return
        
        # Step 2: Only open browser if we have a signal
        print("\n🚨 TRADE SIGNAL DETECTED!")
        success = self.execute_trade_browser(signal)
        
        if success:
            self.trades_today += 1
            print(f"\n✅ Trade #{self.trades_today} processed!")
        else:
            print(f"\n⚠️  Trade execution failed or incomplete")
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously - memory efficient."""
        print(f"🤖 SMART MODE ACTIVATED")
        print(f"⏱️  Checking every {check_interval} seconds")
        print(f"💾 Browser opens ONLY when trading (saves memory)")
        print(f"🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_cycle()
                print(f"\n💤 Next check in {check_interval}s...")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Trading stopped by user")
            print(f"Final Capital: ${self.capital:.2f}")
            print(f"Trades Today: {self.trades_today}")


def main():
    """Main entry point."""
    print()
    print("⚡" * 35)
    print()
    print("     SMART BROWSER MODE")
    print("     Memory Efficient - Opens Browser Only When Trading")
    print()
    print("⚡" * 35)
    print()
    
    # Start agent
    agent = SmartTradingAgent(config_path="live_config.json")
    agent.run_continuous(check_interval=60)


if __name__ == "__main__":
    main()
