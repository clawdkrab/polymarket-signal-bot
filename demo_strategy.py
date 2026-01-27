#!/usr/bin/env python3
"""
Strategy Demo - Show Trading Logic Without Real Markets
Fetches live BTC data and demonstrates what the agent would do.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.price_feed import BTCPriceFeed
from indicators.technical import analyze_price_action
from trading.risk_manager import RiskManager


def main():
    """Demonstrate strategy logic with live BTC data."""
    print("="*70)
    print("STRATEGY DEMO - DECISION LOGIC TEST")
    print("="*70)
    print("Fetching live BTC data and showing what the agent would decide...")
    print()
    
    # Initialize components
    feed = BTCPriceFeed()
    risk_mgr = RiskManager(initial_capital=100.0)
    
    # Get live prices
    print("📊 Fetching BTC price data...")
    hourly_prices = feed.get_recent_prices(240)  # 4 hours
    
    if not hourly_prices or len(hourly_prices) < 20:
        print("❌ Insufficient price data")
        return
    
    current_price = hourly_prices[-1]
    print(f"✅ Got {len(hourly_prices)} hourly prices")
    print(f"   Current BTC: ${current_price:,.2f}")
    print()
    
    # Estimate 15-min prices (interpolation)
    print("🔄 Estimating 15-min candles from hourly data...")
    prices_15m = []
    for i in range(len(hourly_prices) - 1):
        start = hourly_prices[i]
        end = hourly_prices[i + 1]
        for j in range(4):
            prices_15m.append(start + (end - start) * (j / 4))
    prices_15m.append(hourly_prices[-1])
    
    print(f"✅ Estimated {len(prices_15m)} 15-min prices")
    print()
    
    # Run technical analysis
    print("📈 TECHNICAL ANALYSIS")
    print("-" * 70)
    analysis = analyze_price_action(prices_15m)
    
    print(f"RSI:           {analysis['rsi']:.1f}")
    print(f"Momentum:      {analysis['momentum']:+.2f}%")
    print(f"Volatility:    {analysis['volatility']:.2f}%")
    print(f"Trend:         {analysis['trend']['trend']} (strength: {analysis['trend']['strength']:.1f})")
    print()
    
    # Signal generation
    signal = analysis['signal']
    confidence = analysis['confidence']
    
    print("🎯 SIGNAL GENERATION")
    print("-" * 70)
    print(f"Signal:        {signal}")
    print(f"Confidence:    {confidence}%")
    print()
    
    # Risk check
    print("🛡️  RISK MANAGEMENT")
    print("-" * 70)
    
    capital = 100.0
    should_trade, reason = risk_mgr.should_trade(
        capital=capital,
        confidence=confidence,
        daily_pnl=0.0
    )
    
    if not should_trade:
        print(f"❌ Trade BLOCKED: {reason}")
        print()
        print("="*70)
        print("FINAL DECISION: PASS (risk check failed)")
        print("="*70)
        return
    
    print(f"✅ Risk checks passed: {reason}")
    print()
    
    # Position sizing
    if signal != "NEUTRAL" and confidence >= 60:
        position_size = risk_mgr.calculate_position_size(
            capital=capital,
            confidence=confidence,
            recent_pnl=0.0,
            win_streak=0,
            loss_streak=0
        )
        
        print("💰 POSITION SIZING")
        print("-" * 70)
        print(f"Capital:       ${capital:.2f}")
        print(f"Position:      ${position_size:.2f} ({position_size/capital*100:.1f}% of capital)")
        print()
        
        print("="*70)
        print(f"FINAL DECISION: {signal} ${position_size:.2f} @ {confidence}% confidence")
        print("="*70)
        print()
        
        print("📋 TRADE DETAILS")
        print("-" * 70)
        print(f"Direction:     {signal}")
        print(f"Size:          ${position_size:.2f}")
        print(f"Confidence:    {confidence}%")
        print(f"Reasoning:     RSI {analysis['rsi']:.1f} | Momentum {analysis['momentum']:+.2f}% | Trend {analysis['trend']['trend']}")
        
    else:
        print("="*70)
        print(f"FINAL DECISION: PASS (signal: {signal}, confidence: {confidence}%)")
        print("="*70)
        print()
        print("📋 REASONING")
        print("-" * 70)
        if signal == "NEUTRAL":
            print("No clear directional edge detected")
        elif confidence < 60:
            print(f"Confidence too low ({confidence}% < 60% threshold)")
        print()
        print("Sitting out is a valid decision. Waiting for better setup.")


if __name__ == "__main__":
    main()
