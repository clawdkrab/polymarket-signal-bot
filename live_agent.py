#!/usr/bin/env python3
"""
LIVE TRADING AGENT - $300 REAL CAPITAL
Autonomous trading on Polymarket with maximum capital preservation.
"""
import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.polymarket_client import PolymarketClient
from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


def load_credentials():
    """Load API credentials from env vars (Replit) or file (local)."""
    # Try environment variables first (Replit Secrets)
    api_key = os.getenv("POLYMARKET_API_KEY")
    secret = os.getenv("POLYMARKET_SECRET")
    passphrase = os.getenv("POLYMARKET_PASSPHRASE")
    
    if api_key and secret and passphrase:
        print("✅ Credentials loaded from environment variables")
        return {
            "api_key": api_key,
            "secret": secret,
            "passphrase": passphrase
        }
    
    # Fall back to file
    creds_path = Path.home() / ".polymarket_credentials.json"
    if creds_path.exists():
        with open(creds_path) as f:
            print("✅ Credentials loaded from file")
            return json.load(f)
    
    raise ValueError("No credentials found! Set env vars or create ~/.polymarket_credentials.json")


class LiveTradingAgent:
    """Live trading agent with strict risk management."""
    
    def __init__(self, config_path: str = "live_config.json", credentials: dict = None):
        # Load config
        with open(config_path) as f:
            self.config = json.load(f)
        
        assert self.config["mode"] == "LIVE", "Config must be set to LIVE mode"
        
        self.capital = self.config["capital"]
        self.initial_capital = self.capital
        
        # Initialize with credentials
        self.client = PolymarketClient(credentials=credentials)
        self.price_feed = BTCPriceFeed()
        self.risk_manager = RiskManager(initial_capital=self.capital)
        
        # Override risk manager with stricter live settings
        self.risk_manager.max_position_pct = self.config["risk_settings"]["max_position_pct"]
        self.risk_manager.base_position_pct = self.config["risk_settings"]["base_position_pct"]
        
        # State
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Compounding enabled by default
        self.compound_profits = True
        
        print("="*70)
        print("⚠️  LIVE TRADING MODE - REAL CAPITAL")
        print("="*70)
        print(f"Capital: ${self.capital:.2f}")
        print(f"Max Position: {self.config['risk_settings']['max_position_pct']*100:.0f}%")
        print(f"Min Confidence: {self.config['risk_settings']['min_confidence']}%")
        print(f"Max Daily Loss: {self.config['risk_settings']['max_daily_loss_pct']*100:.0f}%")
        print(f"Compounding: {'ENABLED ✅' if self.compound_profits else 'DISABLED'}")
        print("="*70)
        print()
        print("⚠️  CAPITAL PRESERVATION IS PRIORITY #1")
        print("⚠️  ONLY HIGH-CONFIDENCE TRADES")
        print("⚠️  NO REVENGE TRADING")
        print("⚠️  PROFITS COMPOUND AUTOMATICALLY")
        print()
        print("="*70)
        print()
    
    def find_tradeable_markets(self):
        """Find active crypto markets we can trade."""
        print("🔍 Searching for tradeable markets...")
        
        # Get all active markets (closed=False)
        all_markets = self.client.get_markets(limit=500, closed=False)
        
        # Filter for crypto markets
        crypto_markets = []
        btc_markets_debug = []
        
        for market in all_markets:
            if not market.get("active") or market.get("closed"):
                continue
            
            question = market.get("question", "").lower()
            description = market.get("description", "").lower()
            
            # Debug: collect all BTC markets
            if any(kw in question for kw in ["btc", "bitcoin"]):
                btc_markets_debug.append(question)
            
            # Must contain crypto keywords
            has_crypto = any(kw in question for kw in self.config["trading_rules"]["preferred_markets"] + 
                           self.config["trading_rules"]["backup_markets"])
            
            # Must NOT be long-term junk
            is_longterm = any(kw in question for kw in self.config["trading_rules"]["avoid_keywords"])
            
            if has_crypto and not is_longterm:
                # Check if it has reasonable volume
                volume = float(market.get("volume", 0))
                if volume > 1000:  # At least $1k volume
                    crypto_markets.append(market)
        
        print(f"✅ Found {len(crypto_markets)} tradeable BTC markets")
        
        # Debug: show what BTC markets exist
        if len(crypto_markets) == 0 and btc_markets_debug:
            print(f"\n🔍 DEBUG: Found {len(btc_markets_debug)} BTC markets total (none matched filters):")
            for q in btc_markets_debug[:5]:
                print(f"   - {q}")
            print(f"\n⚠️  All filtered out by avoid_keywords")
        
        if crypto_markets:
            print("\nTop markets by volume:")
            sorted_markets = sorted(crypto_markets, key=lambda m: float(m.get("volume", 0)), reverse=True)
            for i, m in enumerate(sorted_markets[:5], 1):
                print(f"  {i}. {m.get('question')}")
                print(f"     Volume: ${float(m.get('volume', 0)):,.0f}")
        
        return crypto_markets
    
    def analyze_market(self, market: dict) -> dict:
        """Analyze a market and generate signal."""
        # Get BTC price data
        hourly_prices = self.price_feed.get_recent_prices(minutes=240)
        
        if not hourly_prices or len(hourly_prices) < 20:
            return {
                "action": "PASS",
                "confidence": 0,
                "reasoning": "Insufficient price data"
            }
        
        # Interpolate to 15-min
        prices_15m = self.price_feed.estimate_15min_prices(hourly_prices)
        
        # Technical analysis
        analysis = analyze_price_action(prices_15m)
        
        signal = analysis["signal"]
        confidence = analysis["confidence"]
        
        # LIVE MODE: Stricter confidence requirement
        min_conf = self.config["risk_settings"]["min_confidence"]
        if confidence < min_conf:
            return {
                "action": "PASS",
                "confidence": confidence,
                "reasoning": f"Confidence {confidence}% < {min_conf}% threshold"
            }
        
        # Risk check
        should_trade, risk_reason = self.risk_manager.should_trade(
            capital=self.capital,
            confidence=confidence,
            daily_pnl=self.daily_pnl
        )
        
        if not should_trade:
            return {
                "action": "PASS",
                "confidence": confidence,
                "reasoning": f"Risk check failed: {risk_reason}"
            }
        
        # Check daily trade limit
        if self.trades_today >= self.config["trading_rules"]["max_trades_per_day"]:
            return {
                "action": "PASS",
                "confidence": confidence,
                "reasoning": "Daily trade limit reached"
            }
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            capital=self.capital,
            confidence=confidence,
            recent_pnl=self.daily_pnl,
            win_streak=0,
            loss_streak=0
        )
        
        # Minimum trade size
        if position_size < self.config["trading_rules"]["min_trade_size"]:
            return {
                "action": "PASS",
                "confidence": confidence,
                "reasoning": f"Position ${position_size:.2f} < ${self.config['trading_rules']['min_trade_size']:.2f} minimum"
            }
        
        return {
            "action": signal,
            "confidence": confidence,
            "size": position_size,
            "reasoning": f"RSI {analysis['rsi']:.1f} | Momentum {analysis['momentum']:+.2f}% | Trend {analysis['trend']['trend']}",
            "analysis": analysis
        }
    
    def execute_trade(self, market: dict, signal: dict):
        """Execute a live trade (REAL MONEY)."""
        print(f"\n🚨 PREPARING TO EXECUTE REAL TRADE")
        print(f"   Market: {market.get('question')}")
        print(f"   Direction: {signal['action']}")
        print(f"   Size: ${signal['size']:.2f}")
        print(f"   Confidence: {signal['confidence']}%")
        print(f"   Reasoning: {signal['reasoning']}")
        print()
        
        # Final safety check
        print("⚠️  FINAL SAFETY CHECK:")
        print(f"   Current Capital: ${self.capital:.2f}")
        print(f"   Risk Amount: ${signal['size']:.2f} ({signal['size']/self.capital*100:.1f}%)")
        print(f"   Remaining if Loss: ${self.capital - signal['size']:.2f}")
        print()
        
        # TODO: Implement actual order execution
        # For now, log the decision
        print("🚨 LIVE EXECUTION NOT YET ENABLED")
        print("   (Would place real order here)")
        print()
        
        # Log to memory
        trade_log = Path(__file__).parent / "src" / "memory" / "live_trades.jsonl"
        trade_log.parent.mkdir(exist_ok=True)
        
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "market": market.get("question"),
            "slug": market.get("slug"),
            "action": signal["action"],
            "size": signal["size"],
            "confidence": signal["confidence"],
            "reasoning": signal["reasoning"],
            "capital_before": self.capital,
            "executed": False  # Set to True when real execution enabled
        }
        
        with open(trade_log, 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
        
        print("✅ Trade logged (execution disabled for safety)")
    
    def check_and_update_capital(self):
        """Check balance and update capital (for compounding)."""
        if not self.compound_profits:
            return
            
        try:
            balance = self.client.get_balance()
            current_usdc = float(balance.get("usdc", 0))
            
            if current_usdc > 0:
                # Calculate profit/loss
                pnl = current_usdc - self.initial_capital
                self.total_pnl = pnl
                
                # Update capital with current balance (compounding)
                old_capital = self.capital
                self.capital = current_usdc
                
                if abs(self.capital - old_capital) > 0.01:
                    change = self.capital - old_capital
                    print(f"💰 Capital updated: ${old_capital:.2f} → ${self.capital:.2f} ({change:+.2f})")
                    print(f"   Total P&L: ${self.total_pnl:+.2f} ({self.total_pnl/self.initial_capital*100:+.1f}%)")
        except Exception as e:
            # Balance check failed - just use manual capital tracking
            pass
    
    def run_cycle(self):
        """Run one trading cycle."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting cycle...")
        
        # Update capital from balance (compounding)
        self.check_and_update_capital()
        
        print(f"Capital: ${self.capital:.2f} | Daily P&L: ${self.daily_pnl:+.2f} | Trades: {self.trades_today}")
        print()
        
        # Find markets
        markets = self.find_tradeable_markets()
        
        if not markets:
            print("⚠️  No tradeable markets found. Waiting...")
            return
        
        # Analyze top market
        market = sorted(markets, key=lambda m: float(m.get("volume", 0)), reverse=True)[0]
        print(f"\n📊 Analyzing: {market.get('question')}")
        
        signal = self.analyze_market(market)
        
        if signal["action"] == "PASS":
            print(f"   ⏸️  PASS - {signal['reasoning']}")
        else:
            self.execute_trade(market, signal)
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously (check every minute by default)."""
        print(f"🤖 LIVE MODE ACTIVATED")
        print(f"⏱️  Checking markets every {check_interval} seconds")
        print(f"🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_cycle()
                print(f"\n💤 Next check in {check_interval}s...")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Live trading stopped by user")
            print(f"Final Capital: ${self.capital:.2f}")
            print(f"Daily P&L: ${self.daily_pnl:+.2f}")


def main():
    """Main entry point."""
    print()
    print("⚠️" * 35)
    print()
    print("     LIVE MODE - MONITORING FOR BTC MARKETS")
    print()
    print("⚠️" * 35)
    print()
    
    # Load credentials
    try:
        creds = load_credentials()
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        print()
        print("For Replit: Add these secrets in the Secrets tab:")
        print("  - POLYMARKET_API_KEY")
        print("  - POLYMARKET_SECRET")
        print("  - POLYMARKET_PASSPHRASE")
        return
    
    # Start agent
    agent = LiveTradingAgent(config_path="live_config.json", credentials=creds)
    agent.run_continuous(check_interval=60)  # Check every 60 seconds


if __name__ == "__main__":
    main()
