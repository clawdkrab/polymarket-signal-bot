#!/usr/bin/env python3
"""
FULLY AUTOMATED BROWSER TRADING AGENT
Hands-free trading with automatic execution
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


class AutoTradingAgent:
    """Fully automated trading via browser."""
    
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
        self.context = None
        self.page = None
        
        print("="*70)
        print("🤖 FULLY AUTOMATED TRADING MODE - REAL CAPITAL")
        print("="*70)
        print(f"Capital: ${self.capital:.2f}")
        print(f"Max Position: {self.config['risk_settings']['max_position_pct']*100:.0f}%")
        print(f"Min Confidence: {self.config['risk_settings']['min_confidence']}%")
        print(f"Headless: {self.headless}")
        print("="*70)
        print()
        print("⚡ FULLY AUTOMATED - NO MANUAL INTERVENTION")
        print("⚠️  WILL EXECUTE TRADES AUTOMATICALLY")
        print("⚠️  MAKE SURE WALLET IS CONNECTED FIRST")
        print()
        print("="*70)
        print()
    
    def start_browser(self):
        """Launch browser with persistent context."""
        print("🚀 Starting browser...")
        
        try:
            self.playwright = sync_playwright().start()
            
            # Launch with persistent context to save wallet connection
            user_data_dir = Path.home() / ".polymarket_browser_data"
            user_data_dir.mkdir(exist_ok=True)
            
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=self.headless,
                viewport={"width": 1280, "height": 720}
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            print("✅ Browser started with persistent session")
            
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            sys.exit(1)
    
    def stop_browser(self):
        """Close browser."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser closed")
    
    def check_wallet_connection(self):
        """Check if wallet is connected, prompt if not."""
        print("🔍 Checking wallet connection...")
        
        try:
            # Navigate to Polymarket
            self.page.goto("https://polymarket.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Look for wallet address or connect button
            page_text = self.page.inner_text('body').lower()
            
            if "connect wallet" in page_text or "sign in" in page_text:
                print()
                print("⚠️" * 35)
                print()
                print("   WALLET NOT CONNECTED!")
                print()
                print("   Please connect your wallet manually:")
                print("   1. Click 'Connect Wallet' in the browser")
                print("   2. Connect MetaMask or your wallet")
                print("   3. Press ENTER here when done")
                print()
                print("⚠️" * 35)
                print()
                
                input("Press ENTER after connecting wallet...")
                
                # Verify connection
                time.sleep(2)
                page_text = self.page.inner_text('body').lower()
                
                if "connect wallet" in page_text:
                    print("❌ Wallet still not connected. Exiting.")
                    return False
                
                print("✅ Wallet connected!")
                return True
            else:
                print("✅ Wallet appears to be connected")
                return True
                
        except Exception as e:
            print(f"⚠️  Error checking wallet: {e}")
            return False
    
    def find_15min_markets(self):
        """Find active 15-minute BTC markets."""
        print("🔍 Scanning for 15-minute markets...")
        
        try:
            # Navigate to crypto markets
            self.page.goto("https://polymarket.com/markets/crypto", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Find all market links
            markets = []
            
            # Look for links containing BTC/bitcoin keywords
            links = self.page.query_selector_all('a')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().lower()
                    
                    # Check if it's a Bitcoin Up/Down market
                    if href and ('btc' in href or 'bitcoin' in text):
                        if 'up' in text or 'down' in text or 'updown' in href:
                            full_url = f"https://polymarket.com{href}" if href.startswith('/') else href
                            markets.append({
                                'url': full_url,
                                'text': text.strip()[:100]
                            })
                except:
                    pass
            
            # Deduplicate by URL
            seen = set()
            unique_markets = []
            for m in markets:
                if m['url'] not in seen:
                    seen.add(m['url'])
                    unique_markets.append(m)
            
            print(f"{'✅' if unique_markets else '⚠️ '} Found {len(unique_markets)} potential markets")
            
            for m in unique_markets[:5]:
                print(f"   - {m['text'][:80]}")
            
            return unique_markets
            
        except Exception as e:
            print(f"❌ Error scanning: {e}")
            return []
    
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
    
    def execute_trade_auto(self, market_url: str, signal: dict):
        """
        FULLY AUTOMATED TRADE EXECUTION
        Navigate to market and execute trade automatically.
        """
        print(f"\n{'='*70}")
        print(f"🚨 EXECUTING AUTOMATED TRADE")
        print(f"{'='*70}")
        print(f"Direction: {signal['action']}")
        print(f"Confidence: {signal['confidence']}%")
        print(f"Size: ${signal['size']:.2f}")
        print(f"Market: {market_url}")
        print(f"{'='*70}\n")
        
        try:
            # Navigate to market
            print("🧭 Navigating to market...")
            self.page.goto(market_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Determine which outcome to bet on
            # Signal is "UP" or "DOWN" - need to click appropriate button
            direction = signal['action'].upper()
            amount = signal['size']
            
            print(f"🎯 Looking for {direction} button...")
            
            # Try to find and click the appropriate outcome button
            # Polymarket typically has "Yes" and "No" buttons, or "Up" and "Down"
            
            # Method 1: Look for exact text match
            button_texts = ["Up", "up", "UP", "Yes", "YES"] if direction == "UP" else ["Down", "down", "DOWN", "No", "NO"]
            
            button_found = False
            for btn_text in button_texts:
                try:
                    # Try to find button with this text
                    button = self.page.get_by_text(btn_text, exact=True).first
                    if button:
                        print(f"✅ Found button: {btn_text}")
                        button.click(timeout=5000)
                        button_found = True
                        time.sleep(1)
                        break
                except:
                    pass
            
            if not button_found:
                # Method 2: Try finding by role
                try:
                    if direction == "UP":
                        button = self.page.get_by_role("button").filter(has_text="Up").first
                    else:
                        button = self.page.get_by_role("button").filter(has_text="Down").first
                    
                    button.click(timeout=5000)
                    button_found = True
                    time.sleep(1)
                    print(f"✅ Clicked {direction} button")
                except:
                    pass
            
            if not button_found:
                print(f"⚠️  Could not find {direction} button - skipping trade")
                return False
            
            # Enter amount
            print(f"⌨️  Entering amount: ${amount:.2f}")
            
            # Find amount input field
            try:
                # Try common selectors for amount input
                amount_input = None
                
                # Try by placeholder
                try:
                    amount_input = self.page.get_by_placeholder("Amount").first
                except:
                    pass
                
                # Try by type
                if not amount_input:
                    try:
                        amount_input = self.page.locator('input[type="number"]').first
                    except:
                        pass
                
                if amount_input:
                    amount_input.fill(str(amount))
                    time.sleep(1)
                    print("✅ Amount entered")
                else:
                    print("⚠️  Could not find amount input field")
                    return False
                    
            except Exception as e:
                print(f"⚠️  Error entering amount: {e}")
                return False
            
            # Click buy/confirm button
            print("🖱️  Clicking buy button...")
            
            try:
                # Look for Buy, Confirm, Place Order, etc.
                buy_button = None
                
                for text in ["Buy", "Confirm", "Place Order", "Submit"]:
                    try:
                        buy_button = self.page.get_by_role("button").filter(has_text=text).first
                        if buy_button:
                            buy_button.click(timeout=5000)
                            print(f"✅ Clicked {text} button")
                            break
                    except:
                        pass
                
                if not buy_button:
                    print("⚠️  Could not find buy/confirm button")
                    return False
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️  Error clicking buy: {e}")
                return False
            
            # Wait for MetaMask popup and auto-confirm
            print("⏳ Waiting for wallet confirmation...")
            
            try:
                # MetaMask will open in a new window/popup
                # We need to switch to it and click confirm
                
                # Wait a bit for popup to appear
                time.sleep(3)
                
                # Check for new pages (MetaMask popup)
                if len(self.context.pages) > 1:
                    print("🔐 MetaMask popup detected")
                    metamask_page = self.context.pages[-1]  # Latest page
                    
                    # Look for Confirm button
                    try:
                        confirm_btn = metamask_page.get_by_role("button").filter(has_text="Confirm").first
                        confirm_btn.click(timeout=10000)
                        print("✅ Auto-confirmed in MetaMask!")
                        time.sleep(3)
                    except:
                        print("⚠️  Could not auto-confirm MetaMask - may need manual confirmation")
                        # Give user 30 seconds to manually confirm
                        print("⏳ Waiting 30s for manual confirmation...")
                        time.sleep(30)
                else:
                    print("⚠️  No MetaMask popup detected - trade may have failed")
                    return False
                
            except Exception as e:
                print(f"⚠️  Wallet confirmation issue: {e}")
                return False
            
            # Check for success
            time.sleep(2)
            page_text = self.page.inner_text('body').lower()
            
            if "success" in page_text or "confirmed" in page_text or "filled" in page_text:
                print("✅ TRADE EXECUTED SUCCESSFULLY!")
                
                # Log the trade
                trade_log = Path(__file__).parent / "src" / "memory" / "auto_trades.jsonl"
                trade_log.parent.mkdir(parents=True, exist_ok=True)
                
                trade_data = {
                    "timestamp": datetime.now().isoformat(),
                    "market_url": market_url,
                    "action": signal["action"],
                    "size": signal["size"],
                    "confidence": signal["confidence"],
                    "capital_before": self.capital,
                    "executed": True
                }
                
                with open(trade_log, 'a') as f:
                    f.write(json.dumps(trade_data) + '\n')
                
                self.trades_today += 1
                
                return True
            else:
                print("⚠️  Trade status unclear")
                return False
                
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_cycle(self):
        """Run one trading cycle."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting cycle...")
        print(f"Capital: ${self.capital:.2f} | Trades Today: {self.trades_today}")
        print()
        
        # Find markets
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
        
        # EXECUTE AUTOMATICALLY
        success = self.execute_trade_auto(market['url'], signal)
        
        if success:
            print(f"\n✅ Trade #{self.trades_today} completed!")
        else:
            print(f"\n⚠️  Trade execution failed or incomplete")
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously."""
        print(f"🤖 FULLY AUTOMATED MODE ACTIVATED")
        print(f"⏱️  Checking every {check_interval} seconds")
        print(f"🛑 Press Ctrl+C to stop")
        print()
        
        self.start_browser()
        
        # Check wallet connection first
        if not self.check_wallet_connection():
            print("❌ Cannot proceed without wallet connection")
            self.stop_browser()
            return
        
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
    print("     FULLY AUTOMATED TRADING MODE")
    print("     NO MANUAL INTERVENTION REQUIRED")
    print()
    print("⚠️" * 35)
    print()
    
    # Check for playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed!")
        return
    
    # Start agent
    agent = AutoTradingAgent(config_path="live_config.json", headless=False)
    agent.run_continuous(check_interval=60)


if __name__ == "__main__":
    main()
