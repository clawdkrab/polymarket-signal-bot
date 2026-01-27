#!/usr/bin/env python3
"""
Paper Trading Mode
Test the trading strategy with synthetic BTC 15-minute markets.
"""
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager
from trading.paper_trading import PaperTradingEngine, SyntheticMarket


class PaperTradingAgent:
    """Agent running in paper trading mode."""
    
    def __init__(self, capital: float = 100.0):
        self.feed = BTCPriceFeed()
        self.risk_mgr = RiskManager(initial_capital=capital)
        self.paper_engine = PaperTradingEngine(initial_capital=capital)
        
        self.current_market: SyntheticMarket = None
        self.market_start_price = None
        
        print("="*70)
        print("PAPER TRADING MODE - STRATEGY TESTING")
        print("="*70)
        print(f"Starting Capital: ${capital:.2f}")
        print("Generating synthetic BTC 15-minute markets")
        print("Testing strategy with real price data")
        print("="*70)
        print()
    
    def create_new_market(self):
        """Create a new synthetic 15-minute market."""
        # Get current BTC price
        current_price = self.feed.get_current_price()
        
        if current_price == 0:
            print("⚠️  Could not fetch current BTC price")
            return False
        
        # Create market
        self.current_market = self.paper_engine.create_market(
            current_price=current_price,
            duration_minutes=15
        )
        self.market_start_price = current_price
        
        print(f"\n📊 NEW MARKET CREATED")
        print(f"   Question: {self.current_market.question}")
        print(f"   Start Price: ${current_price:,.2f}")
        print(f"   Duration: 15 minutes")
        print(f"   Closes at: {self.current_market.end_time.strftime('%H:%M:%S')}")
        print()
        
        return True
    
    def analyze_and_trade(self):
        """Run analysis and place trade if signal is good."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Analyzing market...")
        
        # Get price data
        hourly_prices = self.feed.get_recent_prices(minutes=240)  # 4 hours
        
        if not hourly_prices or len(hourly_prices) < 20:
            print("   ⚠️  Insufficient price data")
            return
        
        # Estimate 15-min prices
        prices_15m = self.feed.estimate_15min_prices(hourly_prices)
        
        # Run technical analysis
        analysis = analyze_price_action(prices_15m)
        
        signal = analysis["signal"]
        confidence = analysis["confidence"]
        rsi = analysis["rsi"]
        momentum = analysis["momentum"]
        trend = analysis["trend"]["trend"]
        
        print(f"   📈 RSI: {rsi:.1f} | Momentum: {momentum:+.2f}% | Trend: {trend}")
        print(f"   🎯 Signal: {signal} | Confidence: {confidence}%")
        
        # Risk check
        perf = self.paper_engine.get_performance()
        should_trade, risk_reason = self.risk_mgr.should_trade(
            capital=perf["capital"],
            confidence=confidence,
            daily_pnl=perf["total_pnl"]
        )
        
        if not should_trade:
            print(f"   ⏸️  PASS - {risk_reason}")
            return
        
        if signal == "NEUTRAL" or confidence < 60:
            print(f"   ⏸️  PASS - No clear edge")
            return
        
        # Calculate position size
        position_size = self.risk_mgr.calculate_position_size(
            capital=perf["capital"],
            confidence=confidence,
            recent_pnl=perf["total_pnl"],
            win_streak=0,  # TODO: track streaks
            loss_streak=0
        )
        
        # Place trade
        try:
            trade = self.paper_engine.place_trade(
                market=self.current_market,
                prediction=signal,
                position_size=position_size,
                confidence=confidence
            )
            
            print(f"   🚀 TRADE PLACED!")
            print(f"      Prediction: {signal}")
            print(f"      Size: ${position_size:.2f}")
            print(f"      Shares: {trade.shares:.2f} @ ${trade.entry_price:.3f}")
            print(f"      Confidence: {confidence}%")
            
        except Exception as e:
            print(f"   ❌ Trade failed: {e}")
    
    def resolve_market(self):
        """Resolve the current market and calculate results."""
        if not self.current_market:
            return
        
        # Get end price
        end_price = self.feed.get_current_price()
        
        if end_price == 0:
            print("⚠️  Could not fetch end price")
            return
        
        print(f"\n⏰ MARKET RESOLVING...")
        print(f"   Start: ${self.market_start_price:,.2f}")
        print(f"   End: ${end_price:,.2f}")
        print(f"   Change: {((end_price - self.market_start_price) / self.market_start_price * 100):+.2f}%")
        
        # Resolve
        outcome = self.paper_engine.resolve_market(self.current_market, end_price)
        
        print(f"   ✅ Actual Outcome: {outcome}")
        print()
        
        # Show updated performance
        self.show_performance()
        
        self.current_market = None
    
    def show_performance(self):
        """Display current performance."""
        perf = self.paper_engine.get_performance()
        
        print("="*70)
        print("PERFORMANCE")
        print("="*70)
        print(f"Capital:      ${perf['capital']:.2f}")
        print(f"Total P&L:    ${perf['total_pnl']:+.2f} ({perf['roi']:+.2f}%)")
        print(f"Trades:       {perf['total_trades']}")
        print(f"Wins:         {perf['wins']}")
        print(f"Losses:       {perf['losses']}")
        
        if perf['total_trades'] > 0:
            print(f"Win Rate:     {perf['win_rate']:.1f}%")
        
        print("="*70)
        print()
    
    def run_test_cycle(self, duration_minutes: int = 15, check_interval: int = 5):
        """Run one complete test cycle (create market, analyze, wait, resolve)."""
        # Create market
        if not self.create_new_market():
            return False
        
        # Analyze and potentially place trade
        self.analyze_and_trade()
        
        # Wait for market to "resolve" (in paper mode, we just wait duration)
        print(f"⏳ Waiting {duration_minutes} minutes for market to resolve...")
        print(f"   (Actually waiting {check_interval} seconds for testing)")
        time.sleep(check_interval)
        
        # Resolve market
        self.resolve_market()
        
        return True
    
    def run_continuous(self, num_cycles: int = 10, cycle_delay: int = 5):
        """Run multiple test cycles."""
        print(f"🤖 Running {num_cycles} test cycles")
        print(f"   Each cycle = 1 synthetic 15-min market")
        print(f"   Delay between cycles: {cycle_delay} seconds")
        print()
        
        try:
            for i in range(num_cycles):
                print(f"\n{'='*70}")
                print(f"CYCLE {i+1}/{num_cycles}")
                print(f"{'='*70}")
                
                success = self.run_test_cycle(duration_minutes=15, check_interval=cycle_delay)
                
                if not success:
                    print("❌ Cycle failed, retrying...")
                    time.sleep(2)
                    continue
                
                if i < num_cycles - 1:
                    print(f"\n💤 Next cycle in {cycle_delay} seconds...")
                    time.sleep(cycle_delay)
            
            print("\n\n🎉 TEST COMPLETE!")
            print()
            self.show_performance()
            
        except KeyboardInterrupt:
            print("\n\n⛔ Testing stopped by user")
            self.show_performance()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading Mode")
    parser.add_argument("--capital", type=float, default=100.0, help="Starting capital")
    parser.add_argument("--cycles", type=int, default=10, help="Number of test cycles")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between cycles")
    
    args = parser.parse_args()
    
    agent = PaperTradingAgent(capital=args.capital)
    agent.run_continuous(num_cycles=args.cycles, cycle_delay=args.delay)


if __name__ == "__main__":
    main()
