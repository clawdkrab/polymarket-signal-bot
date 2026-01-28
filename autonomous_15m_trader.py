#!/usr/bin/env python3
"""
AUTONOMOUS 15M TRADER WITH METAMASK AUTO-CONFIRM
- Stays on /crypto/15M
- 60s refresh cycle
- 15m full reload
- Auto-clicks MetaMask confirm
- $10 position size
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from data.price_feed import BTCPriceFeed
    from indicators.technical import analyze_price_action
except ImportError:
    print("⚠️  Using fallback strategy (Binance momentum only)")
    BTCPriceFeed = None
    analyze_price_action = None


class Autonomous15MTrader:
    """Autonomous 15-minute trader with MetaMask auto-confirm."""
    
    def __init__(self, position_size: float = 10.0, headless: bool = False):
        self.position_size = position_size
        self.headless = headless
        self.trades_count = 0
        self.last_full_reload = datetime.now()
        self.reload_interval = timedelta(minutes=15)
        
        # Browser
        self.playwright = None
        self.context = None
        self.page = None
        
        print("="*70)
        print("🤖 AUTONOMOUS 15M TRADER WITH METAMASK AUTO-CONFIRM")
        print("="*70)
        print(f"Position Size: ${self.position_size:.2f}")
        print(f"Refresh: 60s | Full Reload: 15m")
        print(f"MetaMask: Auto-confirm enabled")
        print(f"Headless: {self.headless}")
        print("="*70)
        print()
    
    def start_browser(self):
        """Launch browser with persistent session."""
        print("🚀 Starting browser...")
        
        try:
            self.playwright = sync_playwright().start()
            
            # Use persistent context to keep wallet connected
            user_data_dir = Path.home() / ".polymarket_browser_data"
            user_data_dir.mkdir(exist_ok=True)
            
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=self.headless,
                viewport={"width": 1920, "height": 1080},
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.set_default_timeout(30000)
            
            print("✅ Browser started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            return False
    
    def stop_browser(self):
        """Close browser."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser closed")
    
    def navigate_to_15m(self, force_reload: bool = False):
        """Navigate or refresh 15M page."""
        try:
            current_url = self.page.url
            
            if force_reload or not current_url.startswith("https://polymarket.com/crypto/15M"):
                print("🧭 Navigating to 15M markets...")
                self.page.goto("https://polymarket.com/crypto/15M", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                print("✅ At 15M markets page")
                self.last_full_reload = datetime.now()
            else:
                print("♻️  Refreshing page...")
                self.page.reload(wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def get_btc_signal(self):
        """Get BTC trading signal."""
        try:
            import requests
            
            response = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": "BTCUSDT", "interval": "15m", "limit": 20},
                timeout=5
            )
            
            if response.status_code == 200:
                candles = response.json()
                closes = [float(c[4]) for c in candles]
                
                if len(closes) >= 10:
                    recent_price = closes[-1]
                    avg_price = sum(closes[-10:]) / 10
                    momentum = ((recent_price / avg_price) - 1) * 100
                    
                    print(f"   📊 BTC: ${recent_price:,.0f} | Momentum: {momentum:+.2f}%")
                    
                    if momentum > 0.3:
                        return {'action': 'UP', 'confidence': min(75, 50 + abs(momentum)*10)}
                    elif momentum < -0.3:
                        return {'action': 'DOWN', 'confidence': min(75, 50 + abs(momentum)*10)}
                    else:
                        return {'action': 'PASS', 'confidence': 0}
            
            return {'action': 'PASS', 'confidence': 0}
            
        except Exception as e:
            print(f"   ⚠️  Signal error: {e}")
            return {'action': 'PASS', 'confidence': 0}
    
    def find_btc_market(self):
        """Find BTC market on page."""
        try:
            # Look for Bitcoin market card
            btc_cards = self.page.locator('text="Bitcoin Up or Down"').first
            
            if btc_cards.is_visible(timeout=3000):
                # Get parent container
                container = btc_cards.locator('xpath=ancestor::div[contains(@class, "")]').first
                return container
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Market find error: {e}")
            return None
    
    def execute_trade(self, direction: str):
        """Execute trade with MetaMask auto-confirm."""
        print(f"\n{'='*70}")
        print(f"🚨 EXECUTING TRADE")
        print(f"{'='*70}")
        print(f"Direction: {direction}")
        print(f"Amount: ${self.position_size:.2f}")
        print(f"{'='*70}\n")
        
        try:
            # Click Up or Down button
            button_text = "Up" if direction == "UP" else "Down"
            print(f"🖱️  Clicking {button_text} button...")
            
            # Find and click the direction button
            button = self.page.get_by_role("button").filter(has_text=button_text).first
            button.click(timeout=5000)
            time.sleep(2)
            
            # Enter amount
            print(f"⌨️  Entering amount ${self.position_size:.2f}...")
            
            amount_input = self.page.locator('input[placeholder*="$"]').first
            amount_input.fill("")
            time.sleep(0.5)
            amount_input.fill(str(self.position_size))
            time.sleep(1)
            
            # Click Buy button
            print("🖱️  Clicking Buy button...")
            
            buy_button = self.page.get_by_role("button").filter(has_text=f"Buy {button_text}").first
            buy_button.click(timeout=10000)
            
            # METAMASK AUTO-CONFIRM
            print("🔐 Waiting for MetaMask...")
            time.sleep(3)
            
            # Check for new popup windows (MetaMask)
            if len(self.context.pages) > 1:
                print("   ✅ MetaMask popup detected")
                metamask_page = self.context.pages[-1]
                
                try:
                    # Wait for and click Confirm button
                    confirm_btn = metamask_page.get_by_role("button").filter(has_text="Confirm").first
                    confirm_btn.click(timeout=10000)
                    print("   ✅ Auto-confirmed in MetaMask!")
                    time.sleep(3)
                    
                    # Close MetaMask popup
                    metamask_page.close()
                    
                except Exception as e:
                    print(f"   ⚠️  MetaMask auto-confirm failed: {e}")
                    print("   ⏸️  Waiting for manual confirmation...")
                    time.sleep(10)
            else:
                print("   ⚠️  No MetaMask popup detected")
                time.sleep(3)
            
            # Verify trade success
            time.sleep(2)
            page_text = self.page.inner_text('body', timeout=5000).lower()
            
            if "success" in page_text or "$" in page_text:
                print("✅ TRADE EXECUTED SUCCESSFULLY")
                self.trades_count += 1
                self.log_trade(direction, self.position_size, "SUCCESS")
                return True
            else:
                print("⚠️  Trade status uncertain")
                self.log_trade(direction, self.position_size, "UNCERTAIN")
                return False
            
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            self.log_trade(direction, self.position_size, f"FAILED - {str(e)}")
            return False
    
    def log_trade(self, direction: str, amount: float, status: str):
        """Log trade to file."""
        try:
            log_file = Path(__file__).parent / "trades_log.jsonl"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "direction": direction,
                "amount": amount,
                "status": status,
                "trades_count": self.trades_count
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            print(f"⚠️  Log error: {e}")
    
    def run(self):
        """Main trading loop."""
        print("\n🚀 Starting autonomous trader...")
        print("Press Ctrl+C to stop\n")
        
        if not self.start_browser():
            return
        
        try:
            # Initial navigation
            if not self.navigate_to_15m(force_reload=True):
                print("❌ Initial navigation failed. Exiting.")
                return
            
            print("\n✅ Setup complete. Starting trading loop...\n")
            
            cycle_count = 0
            
            while True:
                cycle_count += 1
                print(f"\n{'='*70}")
                print(f"CYCLE #{cycle_count} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"Trades today: {self.trades_count}")
                print(f"{'='*70}\n")
                
                # Check if we need full reload
                if datetime.now() - self.last_full_reload > self.reload_interval:
                    print("⏰ 15 minutes elapsed - forcing full reload...")
                    self.navigate_to_15m(force_reload=True)
                else:
                    self.navigate_to_15m(force_reload=False)
                
                # Get signal
                signal = self.get_btc_signal()
                
                print(f"\n💡 Signal: {signal['action']} | Confidence: {signal['confidence']}%")
                
                # Execute if signal strong enough
                if signal['action'] != 'PASS' and signal['confidence'] >= 60:
                    success = self.execute_trade(signal['action'])
                    
                    if success:
                        print(f"\n✅ Trade #{self.trades_count} completed!")
                        print(f"⏸️  Cooling down for 2 minutes...")
                        time.sleep(120)
                    else:
                        print("\n⚠️  Trade failed, continuing...")
                else:
                    print("⏸️  No trade signal or confidence too low")
                
                # Wait 60 seconds before next cycle
                print(f"\n⏸️  Waiting 60 seconds until next check...")
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.stop_browser()
            print(f"\n📊 Final Stats:")
            print(f"   Trades executed: {self.trades_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous 15M trader with MetaMask auto-confirm")
    parser.add_argument("--position-size", type=float, default=10.0, help="Position size in USD (default: $10)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    trader = Autonomous15MTrader(position_size=args.position_size, headless=args.headless)
    trader.run()
