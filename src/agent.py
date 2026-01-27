#!/usr/bin/env python3
"""
Autonomous Polymarket BTC Trading Agent
Core decision-making and execution loop.
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data.polymarket_client import PolymarketClient
from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


class TradingAgent:
    """Autonomous BTC trading agent for Polymarket."""
    
    def __init__(self, capital: float = 100.0):
        self.client = PolymarketClient()
        self.price_feed = BTCPriceFeed()
        self.risk_manager = RiskManager(initial_capital=capital)
        
        self.initial_capital = capital
        self.capital = capital
        
        # Memory
        self.memory_dir = Path(__file__).parent / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        self.trade_log = self.memory_dir / "trades.jsonl"
        self.performance_file = self.memory_dir / "performance.json"
        
        # Performance tracking
        self.trades_executed = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        self.win_streak = 0
        self.loss_streak = 0
        self.daily_pnl = 0.0
        
        # Load previous state if exists
        self._load_state()
        
        print("="*70)
        print("POLYMARKET BTC TRADING AGENT - INITIALIZING")
        print("="*70)
        print(f"Starting Capital: ${self.capital:.2f}")
        print(f"Objective: Maximize net profit over 24h while preserving capital")
        print(f"Universe: Bitcoin 15-minute Up/Down markets only")
        print("="*70)
        print()
    
    def _load_state(self):
        """Load previous trading state."""
        if self.performance_file.exists():
            with open(self.performance_file) as f:
                state = json.load(f)
                self.capital = state.get("capital", self.initial_capital)
                self.trades_executed = state.get("trades_executed", 0)
                self.wins = state.get("wins", 0)
                self.losses = state.get("losses", 0)
                self.total_pnl = state.get("total_pnl", 0.0)
    
    def _save_state(self):
        """Save current trading state."""
        state = {
            "capital": self.capital,
            "trades_executed": self.trades_executed,
            "wins": self.wins,
            "losses": self.losses,
            "total_pnl": self.total_pnl,
            "win_rate": (self.wins / self.trades_executed * 100) if self.trades_executed > 0 else 0,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.performance_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _log_trade(self, trade_data: dict):
        """Log trade to jsonl file."""
        with open(self.trade_log, 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
    
    def find_btc_markets(self, flexible: bool = True) -> list:
        """
        Find active Bitcoin markets.
        
        Args:
            flexible: If True, also include other short-term BTC markets
        """
        print("🔍 Searching for BTC markets...")
        
        markets = self.client.search_markets("bitcoin")
        
        # Filter for time-based resolution markets
        btc_markets = []
        for market in markets:
            question = market.get("question", "").lower()
            
            # Look for 15-minute markets first
            if "15" in question and ("minute" in question or "min" in question):
                btc_markets.append(market)
            
            # If flexible mode, also accept other short-term markets
            elif flexible:
                # Accept hourly, daily, or other time-bounded markets
                if any(term in question for term in ["hour", "day", "minute", "min", "close"]):
                    if "bitcoin" in question or "btc" in question:
                        btc_markets.append(market)
        
        print(f"✅ Found {len(btc_markets)} BTC time-based markets")
        
        if btc_markets:
            print("   Markets found:")
            for i, m in enumerate(btc_markets[:5], 1):
                q = m.get("question", "Unknown")
                print(f"   {i}. {q[:70]}...")
        
        return btc_markets
    
    def analyze_market(self, market: dict) -> Dict:
        """
        Analyze a market and generate trading signal.
        
        Returns:
            {
                "action": "UP" | "DOWN" | "PASS",
                "confidence": 0-100,
                "size": position size in $,
                "reasoning": str
            }
        """
        # Get recent BTC prices for technical analysis
        print("   📊 Fetching BTC price data...")
        hourly_prices = self.price_feed.get_recent_prices(minutes=300)  # 5 hours
        
        if not hourly_prices or len(hourly_prices) < 10:
            return {
                "action": "PASS",
                "confidence": 0,
                "size": 0,
                "reasoning": "Insufficient price data for analysis"
            }
        
        # Estimate 15-min prices from hourly data
        prices_15m = self.price_feed.estimate_15min_prices(hourly_prices)
        
        # Run technical analysis
        analysis = analyze_price_action(prices_15m)
        
        signal = analysis["signal"]
        confidence = analysis["confidence"]
        
        # Get market details
        question = market.get("question", "Unknown")
        current_price = prices_15m[-1] if prices_15m else 0
        
        # Check if we should trade
        should_trade, risk_reason = self.risk_manager.should_trade(
            capital=self.capital,
            confidence=confidence,
            daily_pnl=self.daily_pnl
        )
        
        if not should_trade:
            return {
                "action": "PASS",
                "confidence": confidence,
                "size": 0,
                "reasoning": f"Risk check failed: {risk_reason}"
            }
        
        # If signal is not clear enough, PASS
        if signal == "NEUTRAL" or confidence < 60:
            return {
                "action": "PASS",
                "confidence": confidence,
                "size": 0,
                "reasoning": f"No clear edge (Signal: {signal}, Confidence: {confidence}%)"
            }
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            capital=self.capital,
            confidence=confidence,
            recent_pnl=self.total_pnl,
            win_streak=self.win_streak,
            loss_streak=self.loss_streak
        )
        
        # Build reasoning
        rsi = analysis["rsi"]
        momentum = analysis["momentum"]
        trend = analysis["trend"]["trend"]
        
        reasoning = f"RSI: {rsi:.1f} | Momentum: {momentum:+.2f}% | Trend: {trend} | Confidence: {confidence}%"
        
        return {
            "action": signal,  # "UP" or "DOWN"
            "confidence": confidence,
            "size": position_size,
            "reasoning": reasoning,
            "analysis": analysis  # Store full analysis for logging
        }
    
    def execute_trade(self, market: dict, signal: dict):
        """Execute a trade based on signal."""
        if signal["action"] == "PASS":
            return
        
        print(f"🚀 EXECUTING: {signal['action']} | Size: ${signal['size']:.2f}")
        print(f"   Confidence: {signal['confidence']}% | {signal['reasoning']}")
        
        # Extract market info
        question = market.get("question", "Unknown")
        tokens = market.get("tokens", [])
        
        if len(tokens) < 2:
            print("   ❌ Market has insufficient token data, skipping")
            return
        
        # For BTC Up/Down markets:
        # - "UP" signal → buy YES (token 0)
        # - "DOWN" signal → buy YES on opposite outcome (token 1)
        # Polymarket YES/NO tokens depend on market structure
        
        # Determine which token to buy
        # Typically: tokens[0] = YES for the stated outcome, tokens[1] = NO
        if signal["action"] == "UP":
            # Buy YES on "BTC will go up"
            token_id = tokens[0].get("token_id")
            side = "BUY"
        else:  # DOWN
            # Buy YES on "BTC will go down" (or NO on "BTC will go up")
            token_id = tokens[1].get("token_id")
            side = "BUY"
        
        if not token_id:
            print("   ❌ Could not determine token_id, skipping")
            return
        
        # Get current market price
        try:
            midpoint = self.client.get_midpoint(token_id)
            
            # Calculate shares to buy
            # Size = $ amount we want to risk
            # At midpoint price: shares = size / price
            price = midpoint if midpoint > 0 else 0.50  # Default to 50% if no data
            shares = signal["size"] / price
            
            print(f"   Token: {token_id[:8]}...")
            print(f"   Midpoint: ${price:.3f}")
            print(f"   Shares: {shares:.2f}")
            
            # Place order (Market order for speed)
            # Using slightly worse price to ensure fill
            order_price = min(price * 1.02, 0.99)  # 2% slippage, max $0.99
            
            print(f"   Placing order: {side} {shares:.2f} shares @ ${order_price:.3f}...")
            
            # ACTUAL ORDER EXECUTION
            order_result = self.client.place_order(
                token_id=token_id,
                side=side,
                price=order_price,
                size=shares,
                order_type="FOK"  # Fill or Kill
            )
            
            print(f"   ✅ Order placed! ID: {order_result.get('order_id', 'unknown')}")
            
            # Update capital (pessimistic: assume we paid the cost)
            cost = signal["size"]
            self.capital -= cost
            
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "market": question,
                "token_id": token_id,
                "action": signal["action"],
                "side": side,
                "size": signal["size"],
                "shares": shares,
                "price": order_price,
                "confidence": signal["confidence"],
                "reasoning": signal["reasoning"],
                "executed": True,
                "order_id": order_result.get("order_id"),
                "pnl": 0  # Will update after resolution
            }
            
            self._log_trade(trade_data)
            self.trades_executed += 1
            self._save_state()
            
        except Exception as e:
            print(f"   ❌ Order execution failed: {e}")
            
            # Log failed attempt
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "market": question,
                "action": signal["action"],
                "size": signal["size"],
                "confidence": signal["confidence"],
                "reasoning": signal["reasoning"],
                "executed": False,
                "error": str(e),
                "pnl": 0
            }
            
            self._log_trade(trade_data)
    
    def run_cycle(self):
        """Run one trading cycle."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting new cycle...")
        
        # Find markets
        markets = self.find_btc_markets()
        
        if not markets:
            print("⚠️  No BTC 15-min markets found. Waiting...")
            return
        
        # Analyze each market
        for market in markets:
            question = market.get("question", "Unknown")
            print(f"\n📊 Analyzing: {question}")
            
            signal = self.analyze_market(market)
            
            if signal["action"] != "PASS":
                self.execute_trade(market, signal)
            else:
                print(f"   ⏸️  PASS | {signal['reasoning']}")
        
        # Show status
        self.show_status()
    
    def show_status(self):
        """Display current status."""
        print()
        print("="*70)
        print("STATUS")
        print("="*70)
        print(f"Capital: ${self.capital:.2f} (Start: ${self.initial_capital:.2f})")
        print(f"Total P&L: ${self.total_pnl:+.2f} ({(self.total_pnl/self.initial_capital*100):+.1f}%)")
        print(f"Trades: {self.trades_executed} | Wins: {self.wins} | Losses: {self.losses}")
        
        if self.trades_executed > 0:
            win_rate = self.wins / self.trades_executed * 100
            print(f"Win Rate: {win_rate:.1f}%")
        
        print("="*70)
        print()
    
    def run_autonomous(self, check_interval: int = 60):
        """
        Run autonomously forever.
        
        Args:
            check_interval: Seconds between market checks
        """
        print("🤖 AUTONOMOUS MODE ACTIVATED")
        print(f"⏱️  Checking markets every {check_interval} seconds")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_cycle()
                print(f"💤 Sleeping for {check_interval}s...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⛔ Autonomous mode stopped by user")
            self.show_status()
        
        except Exception as e:
            print(f"\n\n❌ ERROR: {e}")
            self.show_status()
            raise


def main():
    """Main entry point."""
    agent = TradingAgent(capital=100.0)
    
    # Start autonomous trading
    agent.run_autonomous(check_interval=60)  # Check every minute


if __name__ == "__main__":
    main()
