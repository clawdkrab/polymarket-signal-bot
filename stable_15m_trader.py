#!/usr/bin/env python3
"""
STABLE 15-MINUTE BTC TRADER
- Stays on https://polymarket.com/crypto/15M
- Refreshes every 60 seconds
- Full reload every 15 minutes (when markets expire)
- Trades directly from market list (no navigation)
- Starts with $10 positions
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
    from trading.risk_manager import RiskManager
except ImportError:
    print("⚠️  Warning: Could not import strategy modules. Using basic logic.")
    BTCPriceFeed = None
    analyze_price_action = None
    RiskManager = None


class Stable15MTrader:
    """Stable 15-minute market trader."""
    
    def __init__(self, position_size: float = 10.0, headless: bool = False):
        self.position_size = position_size
        self.headless = headless
        self.capital = 300.0  # Track total capital
        self.trades_count = 0
        self.last_full_reload = datetime.now()
        self.reload_interval = timedelta(minutes=15)
        
        # Initialize strategy components if available
        if BTCPriceFeed:
            self.price_feed = BTCPriceFeed()
        else:
            self.price_feed = None
        
        if RiskManager:
            self.risk_manager = RiskManager(initial_capital=self.capital)
            self.risk_manager.max_position_pct = 0.05  # 5% max
            self.risk_manager.base_position_pct = 0.033  # 3.3% base ($10 on $300)
        else:
            self.risk_manager = None
        
        # Browser
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        print("="*70)
        print("🎯 STABLE 15-MINUTE BTC TRADER")
        print("="*70)
        print(f"Position Size: ${self.position_size:.2f}")
        print(f"Capital: ${self.capital:.2f}")
        print(f"Check Interval: 60 seconds")
        print(f"Full Reload: Every 15 minutes")
        print(f"Headless: {self.headless}")
        print("="*70)
        print()
    
    def start_browser(self):
        """Launch browser with persistent context."""
        print("🚀 Starting browser...")
        
        try:
            self.playwright = sync_playwright().start()
            
            # Use persistent context to save wallet connection
            user_data_dir = Path.home() / ".polymarket_browser_data"
            user_data_dir.mkdir(exist_ok=True)
            
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=self.headless,
                viewport={"width": 1920, "height": 1080}
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            # Increase default timeout
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
    
    def navigate_to_15m_page(self, force_reload: bool = False):
        """Navigate to 15M markets page."""
        try:
            if force_reload or not self.page.url.startswith("https://polymarket.com/crypto/15M"):
                print("🧭 Navigating to 15M markets...")
                self.page.goto("https://polymarket.com/crypto/15M", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                print("✅ At 15M markets page")
                self.last_full_reload = datetime.now()
            else:
                print("♻️  Soft refresh...")
                self.page.reload(wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def check_wallet_connected(self):
        """Check if wallet is connected."""
        try:
            page_text = self.page.inner_text('body', timeout=5000).lower()
            
            if "connect wallet" in page_text or "sign in" in page_text:
                print()
                print("⚠️" * 35)
                print()
                print("   WALLET NOT CONNECTED!")
                print()
                print("   Connect your wallet in the browser, then press ENTER")
                print()
                print("⚠️" * 35)
                print()
                input("Press ENTER after connecting wallet...")
                return self.check_wallet_connected()  # Re-check
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not verify wallet: {e}")
            return True  # Assume connected and continue
    
    def find_active_markets(self):
        """Find active 15-minute BTC markets on current page."""
        try:
            print("🔍 Scanning for active markets...")
            
            # Get all visible market cards/containers
            # Polymarket typically uses cards or divs containing market info
            
            markets = []
            
            # Strategy 1: Look for market cards with "Up" and "Down" buttons
            market_containers = self.page.query_selector_all('div[class*="market"], article, div[class*="card"]')
            
            for container in market_containers[:20]:  # Limit to first 20 to avoid performance issues
                try:
                    text = container.inner_text(timeout=1000).lower()
                    
                    # Check if this is a BTC/Bitcoin market with Up/Down
                    if ('btc' in text or 'bitcoin' in text) and ('up' in text and 'down' in text):
                        # Try to find Up and Down buttons within this container
                        up_button = container.query_selector('button:has-text("Up"), button:has-text("up"), button:has-text("Yes")')
                        down_button = container.query_selector('button:has-text("Down"), button:has-text("down"), button:has-text("No")')
                        
                        if up_button and down_button:
                            markets.append({
                                'container': container,
                                'up_button': up_button,
                                'down_button': down_button,
                                'text': text[:150]
                            })
                except:
                    continue
            
            print(f"{'✅' if markets else '⚠️ '} Found {len(markets)} active markets")
            
            for i, m in enumerate(markets[:3]):
                print(f"   [{i+1}] {m['text'][:80]}")
            
            return markets
            
        except Exception as e:
            print(f"❌ Error scanning markets: {e}")
            return []
    
    def get_trading_signal(self):
        """Get trading signal (UP/DOWN/PASS)."""
        
        # If we have strategy modules, use them
        if self.price_feed and analyze_price_action:
            try:
                print("📈 Analyzing BTC price action...")
                
                # Get recent prices
                hourly_prices = self.price_feed.get_recent_prices(minutes=240)
                
                if not hourly_prices or len(hourly_prices) < 20:
                    print("   ⚠️  Insufficient price data")
                    return {'action': 'PASS', 'confidence': 0, 'reason': 'Insufficient data'}
                
                # Estimate 15-min prices
                prices_15m = self.price_feed.estimate_15min_prices(hourly_prices)
                
                # Analyze
                analysis = analyze_price_action(prices_15m)
                
                signal = analysis["signal"]
                confidence = analysis["confidence"]
                
                print(f"   Signal: {signal} | Confidence: {confidence}%")
                print(f"   RSI: {analysis['rsi']:.1f} | Momentum: {analysis['momentum']:+.2f}%")
                
                # Only trade if confidence > 60%
                if confidence < 60:
                    return {'action': 'PASS', 'confidence': confidence, 'reason': 'Confidence too low'}
                
                return {
                    'action': signal,
                    'confidence': confidence,
                    'reason': f"RSI {analysis['rsi']:.1f}, Momentum {analysis['momentum']:+.2f}%"
                }
                
            except Exception as e:
                print(f"   ⚠️  Strategy error: {e}")
                return {'action': 'PASS', 'confidence': 0, 'reason': str(e)}
        
        # Fallback: Basic momentum check using Binance API
        try:
            import requests
            
            # Get recent 15-min candles from Binance
            response = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": "BTCUSDT",
                    "interval": "15m",
                    "limit": 20
                },
                timeout=5
            )
            
            if response.status_code == 200:
                candles = response.json()
                closes = [float(c[4]) for c in candles]
                
                if len(closes) >= 10:
                    # Simple momentum: compare recent price to 10-candle average
                    recent_price = closes[-1]
                    avg_price = sum(closes[-10:]) / 10
                    momentum = ((recent_price / avg_price) - 1) * 100
                    
                    print(f"   📊 Simple momentum: {momentum:+.2f}%")
                    
                    # Trade if momentum > 0.5% (up) or < -0.5% (down)
                    if momentum > 0.5:
                        return {'action': 'UP', 'confidence': min(70, 50 + abs(momentum)*10), 'reason': f'Momentum {momentum:+.2f}%'}
                    elif momentum < -0.5:
                        return {'action': 'DOWN', 'confidence': min(70, 50 + abs(momentum)*10), 'reason': f'Momentum {momentum:+.2f}%'}
                    else:
                        return {'action': 'PASS', 'confidence': 0, 'reason': 'Momentum too weak'}
            
            return {'action': 'PASS', 'confidence': 0, 'reason': 'Could not fetch price data'}
            
        except Exception as e:
            print(f"   ⚠️  Fallback strategy failed: {e}")
            return {'action': 'PASS', 'confidence': 0, 'reason': 'No strategy available'}
    
    def execute_trade(self, market: dict, direction: str):
        """Execute trade on a market."""
        print(f"\n{'='*70}")
        print(f"🚨 EXECUTING TRADE")
        print(f"{'='*70}")
        print(f"Direction: {direction}")
        print(f"Amount: ${self.position_size:.2f}")
        print(f"Market: {market['text'][:80]}")
        print(f"{'='*70}\n")
        
        try:
            # Click the appropriate button (Up or Down)
            button = market['up_button'] if direction == 'UP' else market['down_button']
            
            print(f"🖱️  Clicking {direction} button...")
            button.click(timeout=5000)
            time.sleep(2)
            
            # Look for amount input field that appeared
            print("⌨️  Entering amount...")
            
            # Try multiple selectors for amount input
            amount_input = None
            
            try:
                amount_input = self.page.get_by_placeholder("Amount").first
            except:
                pass
            
            if not amount_input:
                try:
                    amount_input = self.page.locator('input[type="number"]').first
                except:
                    pass
            
            if not amount_input:
                try:
                    amount_input = self.page.locator('input[placeholder*="amount" i]').first
                except:
                    pass
            
            if amount_input:
                # Clear and enter amount
                amount_input.fill("")
                time.sleep(0.5)
                amount_input.fill(str(self.position_size))
                time.sleep(1)
                print(f"✅ Entered ${self.position_size:.2f}")
            else:
                print("⚠️  Could not find amount input - trade may not complete")
                return False
            
            # Look for Buy/Submit/Confirm button
            print("🖱️  Looking for confirm button...")
            
            buy_button = None
            for button_text in ["Buy", "Place Order", "Submit", "Confirm", "Trade"]:
                try:
                    buy_button = self.page.get_by_role("button").filter(has_text=button_text).first
                    if buy_button:
                        print(f"✅ Found button: {button_text}")
                        break
                except:
                    continue
            
            if buy_button:
                print("🖱️  Clicking buy button...")
                buy_button.click(timeout=10000)
                time.sleep(3)
                
                # Check for success confirmation
                page_text = self.page.inner_text('body', timeout=3000).lower()
                
                if "success" in page_text or "confirmed" in page_text or "placed" in page_text:
                    print("✅ TRADE EXECUTED SUCCESSFULLY")
                    self.trades_count += 1
                    self.capital -= self.position_size
                    self.log_trade(direction, self.position_size, "SUCCESS")
                    return True
                else:
                    print("⚠️  Trade may not have executed (no confirmation found)")
                    self.log_trade(direction, self.position_size, "UNCERTAIN")
                    return False
            else:
                print("⚠️  Could not find buy/confirm button")
                self.log_trade(direction, self.position_size, "FAILED - No confirm button")
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
                "trades_count": self.trades_count,
                "capital_remaining": self.capital
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            print(f"⚠️  Could not log trade: {e}")
    
    def run(self):
        """Main trading loop."""
        print("\n🚀 Starting stable 15M trader...")
        print("Press Ctrl+C to stop\n")
        
        if not self.start_browser():
            return
        
        try:
            # Initial navigation
            if not self.navigate_to_15m_page(force_reload=True):
                print("❌ Failed to navigate. Exiting.")
                return
            
            # Check wallet
            if not self.check_wallet_connected():
                print("❌ Wallet not connected. Exiting.")
                return
            
            print("\n✅ Setup complete. Starting trading loop...\n")
            
            # Main loop
            cycle_count = 0
            
            while True:
                cycle_count += 1
                print(f"\n{'='*70}")
                print(f"CYCLE #{cycle_count} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*70}\n")
                
                # Check if we need a full reload (every 15 minutes)
                if datetime.now() - self.last_full_reload > self.reload_interval:
                    print("⏰ 15 minutes elapsed - forcing full reload...")
                    self.navigate_to_15m_page(force_reload=True)
                else:
                    # Soft refresh
                    self.navigate_to_15m_page(force_reload=False)
                
                # Find markets
                markets = self.find_active_markets()
                
                if not markets:
                    print("⏸️  No active markets found. Waiting...")
                    time.sleep(60)
                    continue
                
                # Get trading signal
                signal = self.get_trading_signal()
                
                print(f"\n💡 Signal: {signal['action']} | Confidence: {signal['confidence']}% | Reason: {signal['reason']}")
                
                # Execute trade if signal is not PASS
                if signal['action'] != 'PASS' and signal['confidence'] >= 60:
                    # Trade on first available market
                    market = markets[0]
                    
                    # Execute
                    success = self.execute_trade(market, signal['action'])
                    
                    if success:
                        print(f"\n✅ Trade #{self.trades_count} executed!")
                        print(f"   Capital remaining: ${self.capital:.2f}")
                    
                    # Wait 120 seconds after trade before next check
                    print("\n⏸️  Cooling down for 2 minutes after trade...")
                    time.sleep(120)
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
            print(f"   Capital: ${self.capital:.2f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stable 15-minute BTC trader")
    parser.add_argument("--position-size", type=float, default=10.0, help="Position size in USD (default: $10)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    trader = Stable15MTrader(position_size=args.position_size, headless=args.headless)
    trader.run()
