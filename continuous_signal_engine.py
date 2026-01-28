#!/usr/bin/env python3
"""
CONTINUOUS SIGNAL ENGINE
Generates BTC directional predictions for next 15-minute window, 24/7.

Signal is ALWAYS available. This loop NEVER pauses.
"""
import sys
import json
import time
import requests
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from data.price_feed import BTCPriceFeed
    from indicators.technical import analyze_price_action
    ADVANCED_STRATEGY_AVAILABLE = True
except ImportError:
    ADVANCED_STRATEGY_AVAILABLE = False
    print("⚠️  Advanced strategy unavailable, using momentum fallback")


class ContinuousSignalEngine:
    """
    Always-on signal engine.
    Continuously evaluates BTC price action and generates directional predictions.
    """
    
    def __init__(self):
        self.signal_file = Path(__file__).parent / "signal.json"
        self.log_file = Path(__file__).parent / "signals.jsonl"
        self.price_cache: List[float] = []
        self.last_price = 0.0
        self.loop_count = 0
        
        print("="*80)
        print("🔄 CONTINUOUS SIGNAL ENGINE - ALWAYS-ON MODE")
        print("="*80)
        print(f"Signal output: {self.signal_file}")
        print(f"Signal log: {self.log_file}")
        print(f"Advanced strategy: {ADVANCED_STRATEGY_AVAILABLE}")
        print(f"Loop interval: 3 seconds")
        print("="*80)
        print()
    
    def fetch_btc_price_data(self) -> List[float]:
        """
        Fetch recent BTC price data from Binance.
        Returns last 60 closes (15 hours of 15m candles).
        """
        try:
            response = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": "BTCUSDT",
                    "interval": "15m",
                    "limit": 60
                },
                timeout=5
            )
            
            if response.status_code == 200:
                candles = response.json()
                closes = [float(c[4]) for c in candles]
                self.last_price = closes[-1]
                return closes
            
        except Exception as e:
            print(f"⚠️  Price fetch error: {e}")
        
        # Return cached data if fetch fails
        return self.price_cache if self.price_cache else [0.0] * 60
    
    def calculate_advanced_signal(self, prices: List[float]) -> Dict:
        """
        Multi-factor signal generation using all available indicators.
        
        Analyzes:
        - Short-term momentum (30s, 60s, 120s equivalent via 15m interpolation)
        - Momentum acceleration/deceleration
        - Volatility regime (expanding/contracting)
        - Trend bias (micro vs macro)
        - Mean reversion pressure (distance from moving average)
        """
        if len(prices) < 20:
            return {
                "direction": "NO_TRADE",
                "confidence": 0,
                "basis": {"error": "insufficient_data"}
            }
        
        prices_array = np.array(prices)
        current = prices_array[-1]
        
        # === MOMENTUM CALCULATION ===
        # Simulate 30s, 60s, 120s momentum using recent candles
        momentum_30s = ((prices_array[-1] - prices_array[-2]) / prices_array[-2]) * 100 if len(prices_array) >= 2 else 0
        momentum_60s = ((prices_array[-1] - prices_array[-3]) / prices_array[-3]) * 100 if len(prices_array) >= 3 else 0
        momentum_120s = ((prices_array[-1] - prices_array[-5]) / prices_array[-5]) * 100 if len(prices_array) >= 5 else 0
        
        # Momentum acceleration (is momentum increasing or decreasing?)
        momentum_accel = momentum_30s - momentum_120s
        
        # === VOLATILITY ===
        returns = np.diff(prices_array[-20:]) / prices_array[-20:-1]
        volatility_pct = np.std(returns) * 100
        
        # Volatility regime
        vol_recent = np.std(returns[-5:]) * 100 if len(returns) >= 5 else volatility_pct
        volatility_state = "expanding" if vol_recent > volatility_pct else "contracting"
        
        # === TREND BIAS ===
        sma_5 = np.mean(prices_array[-5:])
        sma_20 = np.mean(prices_array[-20:])
        
        if current > sma_5 > sma_20:
            trend_bias = "strong_up"
        elif current < sma_5 < sma_20:
            trend_bias = "strong_down"
        elif current > sma_5:
            trend_bias = "weak_up"
        elif current < sma_5:
            trend_bias = "weak_down"
        else:
            trend_bias = "neutral"
        
        # === MEAN REVERSION PRESSURE ===
        distance_from_sma20 = ((current - sma_20) / sma_20) * 100
        
        if abs(distance_from_sma20) > 1.5:
            mean_reversion_pressure = "high"
        elif abs(distance_from_sma20) > 0.5:
            mean_reversion_pressure = "medium"
        else:
            mean_reversion_pressure = "low"
        
        # === SIGNAL SYNTHESIS ===
        score = 0.0
        
        # Momentum component (40% weight)
        if momentum_30s > 0.2:
            score += 0.4
        elif momentum_30s < -0.2:
            score -= 0.4
        
        # Momentum acceleration (20% weight)
        if momentum_accel > 0.15:
            score += 0.2
        elif momentum_accel < -0.15:
            score -= 0.2
        
        # Trend following (20% weight)
        if trend_bias == "strong_up":
            score += 0.2
        elif trend_bias == "strong_down":
            score -= 0.2
        elif trend_bias == "weak_up":
            score += 0.1
        elif trend_bias == "weak_down":
            score -= 0.1
        
        # Volatility (10% weight) - high vol = more opportunity
        if volatility_state == "expanding" and volatility_pct > 0.5:
            score += 0.1
        
        # Mean reversion adjustment (10% weight) - fade extremes
        if mean_reversion_pressure == "high":
            if distance_from_sma20 > 1.5:
                score -= 0.1  # Fade overbought
            elif distance_from_sma20 < -1.5:
                score += 0.1  # Fade oversold
        
        # === DECISION ===
        direction = "NO_TRADE"
        confidence = 0
        
        threshold = 0.25  # Require 25% score to trade
        
        if score > threshold:
            direction = "UP"
            confidence = min(95, int(50 + (score * 100)))
        elif score < -threshold:
            direction = "DOWN"
            confidence = min(95, int(50 + (abs(score) * 100)))
        
        basis = {
            "momentum_30s": round(momentum_30s, 3),
            "momentum_60s": round(momentum_60s, 3),
            "momentum_120s": round(momentum_120s, 3),
            "momentum_accel": round(momentum_accel, 3),
            "volatility_pct": round(volatility_pct, 3),
            "volatility_state": volatility_state,
            "trend_bias": trend_bias,
            "distance_from_sma20": round(distance_from_sma20, 3),
            "mean_reversion_pressure": mean_reversion_pressure,
            "score": round(score, 3)
        }
        
        return {
            "direction": direction,
            "confidence": confidence,
            "basis": basis
        }
    
    def generate_signal(self) -> Dict:
        """
        Generate current signal for next 15-minute window.
        This is called continuously, every 3 seconds.
        """
        # Fetch fresh price data
        prices = self.fetch_btc_price_data()
        
        if not prices or len(prices) < 20:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "direction": "NO_TRADE",
                "confidence": 0,
                "price": self.last_price,
                "basis": {"error": "insufficient_data"}
            }
        
        # Calculate signal
        signal = self.calculate_advanced_signal(prices)
        
        # Prepare output
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": signal["direction"],
            "confidence": signal["confidence"],
            "price": self.last_price,
            "basis": signal["basis"]
        }
        
        return output
    
    def write_signal(self, signal: Dict):
        """Write signal to disk for trade executor."""
        try:
            with open(self.signal_file, 'w') as f:
                json.dump(signal, f, indent=2)
        except Exception as e:
            print(f"❌ Signal write error: {e}")
    
    def log_signal(self, signal: Dict):
        """Append signal to JSONL log (periodic snapshots only)."""
        try:
            # Only log every 20th signal (1 per minute)
            if self.loop_count % 20 == 0:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(signal) + '\n')
        except Exception as e:
            print(f"⚠️  Log error: {e}")
    
    def run_forever(self):
        """
        Main loop - NEVER STOPS.
        Continuously generates signals every 3 seconds.
        """
        print("🚀 Signal engine starting...\n")
        
        last_direction = None
        last_confidence = 0
        
        try:
            while True:
                self.loop_count += 1
                
                # Generate signal
                signal = self.generate_signal()
                
                # Write to disk immediately
                self.write_signal(signal)
                
                # Log periodically
                self.log_signal(signal)
                
                # Print status if signal changed
                if signal["direction"] != last_direction or abs(signal["confidence"] - last_confidence) > 10:
                    now = datetime.now().strftime("%H:%M:%S")
                    direction = signal["direction"]
                    conf = signal["confidence"]
                    price = signal["price"]
                    
                    print(f"[{now}] 🎯 {direction:8s} | {conf:2d}% | ${price:,.0f} | Loop #{self.loop_count}")
                    
                    # Show basis details
                    basis = signal.get("basis", {})
                    if "momentum_30s" in basis:
                        print(f"         Momentum: {basis['momentum_30s']:+.3f}% (30s) | "
                              f"{basis['momentum_120s']:+.3f}% (120s) | "
                              f"Accel: {basis['momentum_accel']:+.3f}%")
                        print(f"         Trend: {basis['trend_bias']} | "
                              f"Vol: {basis['volatility_state']} ({basis['volatility_pct']:.2f}%) | "
                              f"MR: {basis['mean_reversion_pressure']}")
                    
                    print()
                    
                    last_direction = direction
                    last_confidence = conf
                
                # Wait 3 seconds before next iteration
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n🛑 Signal engine stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error in signal engine: {e}")
            import traceback
            traceback.print_exc()
            
            # Wait and restart
            print("♻️  Restarting in 10 seconds...")
            time.sleep(10)
            self.run_forever()  # Auto-restart


if __name__ == "__main__":
    engine = ContinuousSignalEngine()
    engine.run_forever()
