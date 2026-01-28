#!/usr/bin/env python3
"""
AUTONOMOUS TRADE EXECUTOR
Monitors Polymarket 15M markets and executes trades based on signal.json.
Uses Playwright with persistent Chrome profile (clawdkrab@gmail.com).

This process:
- Stays on https://polymarket.com/crypto/15M
- Polls DOM every 5-10 seconds
- Detects new markets by timestamp change
- Reads signal.json immediately
- Executes trade if confidence >= threshold
- Auto-confirms MetaMask
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class AutonomousTradeExecutor:
    """
    Trade executor that runs independently of chat.
    Reads signals from disk, executes via Playwright.
    """
    
    def __init__(
        self,
        position_size: float = 10.0,
        confidence_threshold: int = 60,
        chrome_profile: str = "Default"
    ):
        self.position_size = position_size
        self.confidence_threshold = confidence_threshold
        self.chrome_profile = chrome_profile
        
        # Paths
        self.signal_file = Path(__file__).parent / "signal.json"
        self.trades_log = Path(__file__).parent / "trades.jsonl"
        self.error_log = Path(__file__).parent / "errors.log"
        
        # State
        self.last_market_timestamp = None
        self.trades_count = 0
        self.last_trade_time = None
        self.cooldown_minutes = 2  # Wait 2 minutes after trade before next
        
        # Browser
        self.playwright = None
        self.context = None
        self.page = None
        
        print("="*80)
        print("⚡ AUTONOMOUS TRADE EXECUTOR - HANDS-FREE MODE")
        print("="*80)
        print(f"Chrome profile: {self.chrome_profile}")
        print(f"Position size: ${self.position_size:.2f}")
        print(f"Confidence threshold: {self.confidence_threshold}%")
        print(f"Signal source: {self.signal_file}")
        print(f"Cooldown: {self.cooldown_minutes} minutes between trades")
        print("="*80)
        print()
    
    def log_error(self, error: str):
        """Log error to file."""
        try:
            with open(self.error_log, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {error}\n")
        except:
            pass
    
    def log_trade(self, direction: str, amount: float, status: str, details: str = ""):
        """Log trade execution."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "direction": direction,
                "amount": amount,
                "status": status,
                "details": details,
                "trades_count": self.trades_count
            }
            
            with open(self.trades_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            self.log_error(f"Trade log error: {e}")
    
    def start_browser(self) -> bool:
        """Launch Playwright with persistent Chrome profile."""
        try:
            print("🚀 Starting Playwright with Chrome profile...")
            
            self.playwright = sync_playwright().start()
            
            # Use existing Chrome profile directory
            chrome_user_data = Path.home() / "Library/Application Support/Google/Chrome"
            
            if not chrome_user_data.exists():
                print(f"❌ Chrome user data dir not found: {chrome_user_data}")
                return False
            
            print(f"   User data dir: {chrome_user_data}")
            print(f"   Profile: {self.chrome_profile}")
            
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(chrome_user_data),
                channel="chrome",  # Use installed Chrome (not Chromium)
                headless=False,  # Must be visible for MetaMask
                args=[
                    f'--profile-directory={self.chrome_profile}',
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security'
                ],
                viewport={"width": 1920, "height": 1080},
                ignore_default_args=["--enable-automation"]
            )
            
            # Get or create page
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            self.page.set_default_timeout(30000)
            
            print("✅ Browser started\n")
            return True
            
        except Exception as e:
            error_msg = f"Browser start failed: {e}"
            print(f"❌ {error_msg}")
            self.log_error(error_msg)
            return False
    
    def stop_browser(self):
        """Close browser context."""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            print("🛑 Browser closed")
        except:
            pass
    
    def navigate_to_crypto_15m(self):
        """Navigate to crypto 15M markets page."""
        try:
            target_url = "https://polymarket.com/crypto/15M"
            
            if self.page.url != target_url:
                print(f"🧭 Navigating to {target_url}...")
                self.page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                print("✅ At crypto/15M page")
            
            return True
            
        except Exception as e:
            error_msg = f"Navigation failed: {e}"
            print(f"❌ {error_msg}")
            self.log_error(error_msg)
            return False
    
    def detect_new_market(self) -> bool:
        """
        Detect if a new 15-minute market has appeared.
        Returns True if new market detected.
        """
        try:
            # Look for market cards with timestamps
            page_html = self.page.content()
            
            # Simple heuristic: look for "in X minutes" or specific time patterns
            # This is a placeholder - adjust based on actual DOM structure
            
            # For now, trigger every 15 minutes on the clock
            now = datetime.now()
            current_minute = now.minute
            
            # Markets appear at :00, :15, :30, :45
            if current_minute in [0, 15, 30, 45]:
                # Check if we already traded this window
                if self.last_market_timestamp:
                    time_since_last = (now - self.last_market_timestamp).total_seconds()
                    if time_since_last < 600:  # Less than 10 minutes
                        return False
                
                print(f"🆕 New market window detected at :{current_minute:02d}")
                self.last_market_timestamp = now
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Market detection error: {e}")
            return False
    
    def read_signal(self) -> dict:
        """Read current signal from disk."""
        try:
            if not self.signal_file.exists():
                return {"direction": "NO_TRADE", "confidence": 0}
            
            with open(self.signal_file, 'r') as f:
                signal = json.load(f)
            
            return signal
            
        except Exception as e:
            self.log_error(f"Signal read error: {e}")
            return {"direction": "NO_TRADE", "confidence": 0}
    
    def check_cooldown(self) -> bool:
        """Check if we're still in cooldown period."""
        if not self.last_trade_time:
            return False
        
        elapsed = (datetime.now() - self.last_trade_time).total_seconds() / 60
        return elapsed < self.cooldown_minutes
    
    def execute_trade(self, direction: str) -> bool:
        """
        Execute trade on Polymarket with MetaMask auto-confirm.
        
        Args:
            direction: "UP" or "DOWN"
        
        Returns:
            True if trade successful
        """
        print(f"\n{'='*80}")
        print(f"💰 EXECUTING TRADE: {direction}")
        print(f"{'='*80}")
        print(f"Amount: ${self.position_size:.2f}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}\n")
        
        try:
            # Step 1: Find and click direction button
            button_text = "Up" if direction == "UP" else "Down"
            print(f"🖱️  Step 1: Clicking {button_text} button...")
            
            try:
                direction_button = self.page.get_by_role("button").filter(has_text=button_text).first
                direction_button.click(timeout=10000)
                time.sleep(2)
                print("   ✅ Direction selected")
            except Exception as e:
                raise Exception(f"Could not find {button_text} button: {e}")
            
            # Step 2: Enter amount
            print(f"⌨️  Step 2: Entering ${self.position_size:.2f}...")
            
            try:
                amount_input = self.page.locator('input[type="number"], input[placeholder*="$"]').first
                amount_input.fill("")
                time.sleep(0.3)
                amount_input.fill(str(self.position_size))
                time.sleep(1)
                print("   ✅ Amount entered")
            except Exception as e:
                raise Exception(f"Could not enter amount: {e}")
            
            # Step 3: Click Buy button
            print(f"🖱️  Step 3: Clicking Buy {button_text} button...")
            
            try:
                buy_button = self.page.get_by_role("button").filter(has_text=f"Buy {button_text}").first
                buy_button.click(timeout=10000)
                time.sleep(3)
                print("   ✅ Buy clicked")
            except Exception as e:
                raise Exception(f"Could not click Buy button: {e}")
            
            # Step 4: Handle MetaMask
            print("🔐 Step 4: Handling MetaMask confirmation...")
            
            success = self.handle_metamask()
            
            if success:
                self.trades_count += 1
                self.last_trade_time = datetime.now()
                
                print(f"\n✅ TRADE #{self.trades_count} EXECUTED SUCCESSFULLY")
                self.log_trade(direction, self.position_size, "SUCCESS", "")
                return True
            else:
                print("\n⚠️  Trade status uncertain")
                self.log_trade(direction, self.position_size, "UNCERTAIN", "MetaMask unclear")
                return False
            
        except Exception as e:
            error_msg = f"Trade execution failed: {e}"
            print(f"\n❌ {error_msg}")
            self.log_error(error_msg)
            self.log_trade(direction, self.position_size, "FAILED", str(e))
            return False
    
    def handle_metamask(self) -> bool:
        """
        Auto-confirm MetaMask popup.
        Returns True if confirmed successfully.
        """
        try:
            # Wait for MetaMask popup
            time.sleep(2)
            
            # Check for new popup/tab
            if len(self.context.pages) > 1:
                print("   🔍 MetaMask popup detected")
                metamask_page = self.context.pages[-1]
                
                try:
                    # Look for unlock screen first
                    metamask_password = os.getenv("METAMASK_PASSWORD", "")
                    
                    if metamask_password:
                        try:
                            password_input = metamask_page.locator('input[type="password"]').first
                            if password_input.is_visible(timeout=2000):
                                print("   🔓 Unlocking MetaMask...")
                                password_input.fill(metamask_password)
                                unlock_btn = metamask_page.get_by_role("button").filter(has_text="Unlock").first
                                unlock_btn.click()
                                time.sleep(2)
                                print("   ✅ MetaMask unlocked")
                        except:
                            pass  # Already unlocked
                    
                    # Click Confirm/Sign button
                    confirm_button = metamask_page.get_by_role("button").filter(
                        has_text=lambda text: text in ["Confirm", "Sign"]
                    ).first
                    
                    confirm_button.click(timeout=15000)
                    print("   ✅ MetaMask confirmed!")
                    time.sleep(2)
                    
                    # Close MetaMask popup
                    metamask_page.close()
                    
                    # Switch back to main page
                    self.page = self.context.pages[0]
                    
                    return True
                    
                except Exception as e:
                    print(f"   ⚠️  MetaMask auto-confirm failed: {e}")
                    print("   ⏳ Waiting 15 seconds for manual confirmation...")
                    time.sleep(15)
                    return False
            else:
                print("   ⚠️  No MetaMask popup detected")
                time.sleep(3)
                return False
                
        except Exception as e:
            self.log_error(f"MetaMask handling error: {e}")
            return False
    
    def poll_and_trade_loop(self):
        """
        Main trading loop.
        Continuously polls page and trades on new markets.
        """
        print("🔄 Starting trade monitoring loop...\n")
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                now = datetime.now().strftime("%H:%M:%S")
                
                print(f"[{now}] Cycle #{cycle} | Trades: {self.trades_count}")
                
                # Ensure we're on the right page
                self.navigate_to_crypto_15m()
                
                # Check for new market
                if self.detect_new_market():
                    print("🎯 New market detected!")
                    
                    # Check cooldown
                    if self.check_cooldown():
                        elapsed = (datetime.now() - self.last_trade_time).total_seconds() / 60
                        remaining = self.cooldown_minutes - elapsed
                        print(f"⏸️  In cooldown: {remaining:.1f} minutes remaining\n")
                        time.sleep(10)
                        continue
                    
                    # Read signal
                    signal = self.read_signal()
                    direction = signal.get("direction", "NO_TRADE")
                    confidence = signal.get("confidence", 0)
                    
                    print(f"📊 Signal: {direction} | Confidence: {confidence}%")
                    
                    # Decide whether to trade
                    if direction in ["UP", "DOWN"] and confidence >= self.confidence_threshold:
                        print(f"✅ Signal meets threshold ({confidence}% >= {self.confidence_threshold}%)")
                        
                        # Execute trade
                        success = self.execute_trade(direction)
                        
                        if success:
                            print(f"\n✨ Trade successful! Cooling down for {self.cooldown_minutes} minutes...\n")
                        else:
                            print("\n⚠️  Trade failed or uncertain. Continuing...\n")
                    else:
                        print(f"⏸️  Signal below threshold or NO_TRADE\n")
                
                # Poll every 10 seconds
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopped by user")
                break
            
            except Exception as e:
                error_msg = f"Loop error: {e}"
                print(f"❌ {error_msg}")
                self.log_error(error_msg)
                
                # Try to recover
                print("♻️  Recovering in 10 seconds...")
                time.sleep(10)
                
                try:
                    self.navigate_to_crypto_15m()
                except:
                    pass
    
    def run_forever(self):
        """
        Main entry point - runs until stopped.
        Auto-restarts browser if it crashes.
        """
        print("🚀 Trade executor starting...\n")
        
        try:
            while True:
                # Start browser
                if not self.start_browser():
                    print("❌ Browser failed to start. Retrying in 30 seconds...")
                    time.sleep(30)
                    continue
                
                # Navigate to page
                if not self.navigate_to_crypto_15m():
                    print("❌ Navigation failed. Restarting browser...")
                    self.stop_browser()
                    time.sleep(10)
                    continue
                
                print("✅ System ready. Monitoring for markets...\n")
                
                # Run trading loop
                try:
                    self.poll_and_trade_loop()
                except Exception as e:
                    print(f"\n❌ Trading loop crashed: {e}")
                    self.log_error(f"Trading loop crash: {e}")
                
                # Clean up and restart
                print("\n♻️  Restarting browser...")
                self.stop_browser()
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Executor stopped by user")
            self.stop_browser()
        
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.log_error(f"Fatal error: {e}")
            self.stop_browser()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Trade Executor")
    parser.add_argument("--position-size", type=float, default=10.0, help="Position size in USD")
    parser.add_argument("--confidence", type=int, default=60, help="Minimum confidence threshold")
    parser.add_argument("--profile", type=str, default="Default", help="Chrome profile name")
    
    args = parser.parse_args()
    
    executor = AutonomousTradeExecutor(
        position_size=args.position_size,
        confidence_threshold=args.confidence,
        chrome_profile=args.profile
    )
    
    executor.run_forever()
