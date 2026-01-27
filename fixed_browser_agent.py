#!/usr/bin/env python3
"""
FIXED BROWSER AGENT
Uses ONLY the clawdkrab@gmail.com Chrome browser (the one with MetaMask)
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


class FixedBrowserAgent:
    """Uses clawdbot browser tool to control existing Chrome."""
    
    def __init__(self, config_path: str = "live_config.json"):
        # Load config
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.capital = self.config["capital"]
        self.initial_capital = self.capital
        
        # Initialize components (lightweight - no browser manipulation yet)
        self.price_feed = BTCPriceFeed()
        self.risk_manager = RiskManager(initial_capital=self.capital)
        
        # Override with stricter live settings
        self.risk_manager.max_position_pct = self.config["risk_settings"]["max_position_pct"]
        self.risk_manager.base_position_pct = self.config["risk_settings"]["base_position_pct"]
        
        # State
        self.trades_today = 0
        
        print("="*70)
        print("🤖 FIXED BROWSER MODE")
        print("="*70)
        print(f"Capital: ${self.capital:.2f}")
        print(f"Min Confidence: {self.config['risk_settings']['min_confidence']}%")
        print()
        print("⚡ Uses YOUR Chrome browser (clawdkrab@gmail.com)")
        print("⚡ MetaMask already connected")
        print("⚡ NO new browsers will be opened")
        print()
        print("="*70)
        print()
    
    def analyze_signal(self):
        """Lightweight analysis - no browser needed."""
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
    
    def execute_trade_manual_assist(self, signal: dict):
        """
        Trade execution with user's Chrome browser.
        Bot will tell user what to do, user executes manually for now.
        """
        print(f"\n{'='*70}")
        print(f"🚨 TRADE SIGNAL DETECTED!")
        print(f"{'='*70}")
        print(f"Direction: {signal['action']}")
        print(f"Confidence: {signal['confidence']}%")
        print(f"Size: ${signal['size']:.2f}")
        print(f"{'='*70}\n")
        
        # Log the signal
        log_file = Path(__file__).parent / "src" / "memory" / "trade_signals.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "action": signal["action"],
            "size": signal["size"],
            "confidence": signal["confidence"],
            "capital_before": self.capital,
            "rsi": signal["analysis"]["rsi"],
            "momentum": signal["analysis"]["momentum"],
            "executed": False,
            "note": "Signal detected - awaiting Clawdbot browser integration"
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
        
        print("✅ Signal logged to trade_signals.jsonl")
        print()
        print("📋 MANUAL EXECUTION INSTRUCTIONS:")
        print(f"   1. Open https://polymarket.com/markets/crypto in your Chrome")
        print(f"   2. Find a Bitcoin 15-minute Up/Down market")
        print(f"   3. Click {'UP' if signal['action'] == 'UP' else 'DOWN'}")
        print(f"   4. Enter amount: ${signal['size']:.2f}")
        print(f"   5. Click Buy/Confirm")
        print(f"   6. Approve MetaMask transaction")
        print()
        print("⚠️  AUTOMATED EXECUTION COMING SOON")
        print("    (Need to integrate Clawdbot browser tool)")
        print()
        
        return True
    
    def run_cycle(self):
        """Run one cycle: analyze, then alert if signal exists."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting cycle...")
        print(f"Capital: ${self.capital:.2f} | Trades Today: {self.trades_today}")
        print()
        
        # Lightweight analysis
        signal = self.analyze_signal()
        
        if not signal:
            print("   ⏸️  No trade signal - monitoring continues")
            return
        
        # Signal detected!
        print("\n🚨 TRADE SIGNAL DETECTED!")
        success = self.execute_trade_manual_assist(signal)
        
        if success:
            print(f"\n✅ Signal #{self.trades_today + 1} processed!")
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously."""
        print(f"🤖 MONITORING ACTIVATED")
        print(f"⏱️  Checking every {check_interval} seconds")
        print(f"🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_cycle()
                print(f"\n💤 Next check in {check_interval}s...")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Monitoring stopped by user")
            print(f"Final Capital: ${self.capital:.2f}")
            print(f"Trades Today: {self.trades_today}")


def main():
    """Main entry point."""
    print()
    print("="*70)
    print("FIXED BROWSER MODE - Uses YOUR Chrome with MetaMask")
    print("="*70)
    print()
    
    agent = FixedBrowserAgent(config_path="live_config.json")
    agent.run_continuous(check_interval=60)


if __name__ == "__main__":
    main()
