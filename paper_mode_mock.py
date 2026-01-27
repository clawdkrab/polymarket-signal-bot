#!/usr/bin/env python3
"""
Paper Trading Mode (Mock Data)
Test strategy with synthetic price data when APIs are unavailable.
"""
import sys
import time
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager
from trading.paper_trading import PaperTradingEngine


class MockPriceFeed:
    """Mock price feed for testing."""
    
    def __init__(self, base_price: float = 88000.0):
        self.base_price = base_price
        self.current_price = base_price
        self.price_history = [base_price]
    
    def generate_realistic_move(self):
        """Generate realistic BTC price movement."""
        # BTC typically moves 0.1-1% in 15 minutes
        change_pct = random.gauss(0, 0.3)  # Mean 0%, StdDev 0.3%
        change = self.current_price * (change_pct / 100)
        self.current_price += change
        self.price_history.append(self.current_price)
        return self.current_price
    
    def get_recent_prices(self, count: int = 50) -> list:
        """Get recent hourly prices."""
        # Generate if needed
        while len(self.price_history) < count:
            self.generate_realistic_move()
        
        return self.price_history[-count:]
    
    def get_current_price(self) -> float:
        """Get current price."""
        return self.current_price


def run_paper_test(cycles: int = 10, starting_capital: float = 100.0):
    """Run paper trading test with mock data."""
    print("="*70)
    print("PAPER TRADING MODE - MOCK DATA TEST")
    print("="*70)
    print(f"Starting Capital: ${starting_capital:.2f}")
    print(f"Test Cycles: {cycles}")
    print("Using synthetic BTC price movements")
    print("="*70)
    print()
    
    # Initialize
    feed = MockPriceFeed(base_price=88000.0)
    risk_mgr = RiskManager(initial_capital=starting_capital)
    engine = PaperTradingEngine(initial_capital=starting_capital)
    
    # Generate initial price history
    print("📊 Generating initial price history...")
    for _ in range(100):
        feed.generate_realistic_move()
    print(f"✅ Generated {len(feed.price_history)} price points")
    print()
    
    # Run cycles
    for cycle in range(1, cycles + 1):
        print(f"\n{'='*70}")
        print(f"CYCLE {cycle}/{cycles}")
        print(f"{'='*70}")
        
        # Get current price and create market
        start_price = feed.get_current_price()
        market = engine.create_market(start_price, duration_minutes=15)
        
        print(f"\n📊 Market: {market.question}")
        print(f"   Start: ${start_price:,.2f}")
        
        # Get price data and analyze
        prices = feed.get_recent_prices(50)
        analysis = analyze_price_action(prices)
        
        signal = analysis["signal"]
        confidence = analysis["confidence"]
        rsi = analysis["rsi"]
        momentum = analysis["momentum"]
        trend = analysis["trend"]["trend"]
        
        print(f"\n📈 Technical Analysis:")
        print(f"   RSI: {rsi:.1f}")
        print(f"   Momentum: {momentum:+.2f}%")
        print(f"   Trend: {trend}")
        print(f"   Signal: {signal}")
        print(f"   Confidence: {confidence}%")
        
        # Risk check
        perf = engine.get_performance()
        should_trade, risk_reason = risk_mgr.should_trade(
            capital=perf["capital"],
            confidence=confidence,
            daily_pnl=perf["total_pnl"]
        )
        
        if not should_trade or signal == "NEUTRAL" or confidence < 60:
            reason = risk_reason if not should_trade else "No clear edge"
            print(f"\n⏸️  PASS - {reason}")
            
            # Still need to resolve market (simulate 15 min passing)
            for _ in range(15):
                feed.generate_realistic_move()
            
            end_price = feed.get_current_price()
            engine.resolve_market(market, end_price)
            
            print(f"   Market resolved: ${end_price:,.2f} ({((end_price-start_price)/start_price*100):+.2f}%)")
            continue
        
        # Calculate position size
        position_size = risk_mgr.calculate_position_size(
            capital=perf["capital"],
            confidence=confidence,
            recent_pnl=perf["total_pnl"],
            win_streak=0,
            loss_streak=0
        )
        
        # Place trade
        trade = engine.place_trade(market, signal, position_size, confidence)
        
        print(f"\n🚀 TRADE PLACED!")
        print(f"   Prediction: {signal}")
        print(f"   Size: ${position_size:.2f}")
        print(f"   Shares: {trade.shares:.2f} @ ${trade.entry_price:.3f}")
        
        # Simulate 15 minutes passing
        print(f"\n⏳ Simulating 15-minute market movement...")
        for _ in range(15):
            feed.generate_realistic_move()
        
        # Resolve
        end_price = feed.get_current_price()
        outcome = engine.resolve_market(market, end_price)
        
        print(f"\n✅ MARKET RESOLVED")
        print(f"   Start: ${start_price:,.2f}")
        print(f"   End: ${end_price:,.2f}")
        print(f"   Change: {((end_price-start_price)/start_price*100):+.2f}%")
        print(f"   Outcome: {outcome}")
        
        # Show trade result
        if trade.resolved:
            result = "✅ WIN" if trade.won else "❌ LOSS"
            print(f"\n{result}")
            print(f"   P&L: ${trade.pnl:+.2f}")
    
    # Final performance
    print(f"\n\n{'='*70}")
    print("FINAL PERFORMANCE")
    print(f"{'='*70}")
    
    perf = engine.get_performance()
    print(f"Starting Capital: ${perf['initial_capital']:.2f}")
    print(f"Ending Capital:   ${perf['capital']:.2f}")
    print(f"Total P&L:        ${perf['total_pnl']:+.2f} ({perf['roi']:+.2f}%)")
    print(f"Total Trades:     {perf['total_trades']}")
    print(f"Wins:             {perf['wins']}")
    print(f"Losses:           {perf['losses']}")
    
    if perf['total_trades'] > 0:
        print(f"Win Rate:         {perf['win_rate']:.1f}%")
        avg_pnl = perf['total_pnl'] / perf['total_trades']
        print(f"Avg P&L/Trade:    ${avg_pnl:+.2f}")
    
    print(f"{'='*70}")
    
    # Summary
    print()
    if perf['capital'] > perf['initial_capital']:
        print("🎉 PROFITABLE! Strategy generated positive returns.")
    elif perf['capital'] == perf['initial_capital']:
        print("😐 BREAK-EVEN - No profit, no loss.")
    else:
        print("📉 UNPROFITABLE - Strategy needs adjustment.")
    
    print()
    print("💾 Trade log saved to: src/memory/paper_trades.jsonl")
    print("💾 State saved to: src/memory/paper_state.json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading with Mock Data")
    parser.add_argument("--cycles", type=int, default=10, help="Number of test cycles")
    parser.add_argument("--capital", type=float, default=100.0, help="Starting capital")
    
    args = parser.parse_args()
    
    run_paper_test(cycles=args.cycles, starting_capital=args.capital)
