#!/usr/bin/env python3
"""
MULTI-ASSET SIGNAL ENGINE
Generates trading signals for BTC, ETH, SOL, and XRP simultaneously.
Ensures 4 signals are always available for Polymarket's 15M markets.
"""
import json
import time
import requests
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List


class MultiAssetSignalEngine:
    """
    Generates signals for all 4 Polymarket 15M markets:
    - Bitcoin (BTC)
    - Ethereum (ETH)
    - Solana (SOL)
    - XRP
    """
    
    ASSETS = {
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'SOL': 'SOLUSDT',
        'XRP': 'XRPUSDT'
    }
    
    def __init__(self):
        self.signals_file = Path(__file__).parent / "signals_all.json"
        self.log_file = Path(__file__).parent / "signals_all.jsonl"
        self.loop_count = 0
        
        print("="*80)
        print("🔄 MULTI-ASSET SIGNAL ENGINE - ALWAYS-ON MODE")
        print("="*80)
        print(f"Assets: BTC, ETH, SOL, XRP")
        print(f"Output: {self.signals_file}")
        print(f"Log: {self.log_file}")
        print(f"Loop: 3 seconds")
        print("="*80)
        print()
    
    def fetch_asset_prices(self, symbol: str, limit: int = 60) -> List[float]:
        """
        Fetch recent price data from Binance.
        Returns last N closes (15m candles).
        """
        try:
            response = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": symbol,
                    "interval": "15m",
                    "limit": limit
                },
                timeout=5
            )
            
            if response.status_code == 200:
                candles = response.json()
                closes = [float(c[4]) for c in candles]
                return closes
            
        except Exception as e:
            print(f"⚠️  Error fetching {symbol}: {e}")
        
        return []
    
    def calculate_signal(self, prices: List[float]) -> Dict:
        """
        Multi-factor signal generation.
        Same logic as continuous_signal_engine but modularized.
        """
        if len(prices) < 20:
            return {
                "direction": "NO_TRADE",
                "confidence": 0,
                "basis": {"error": "insufficient_data"}
            }
        
        prices_array = np.array(prices)
        current = prices_array[-1]
        
        # === MOMENTUM ===
        momentum_30s = ((prices_array[-1] - prices_array[-2]) / prices_array[-2]) * 100 if len(prices_array) >= 2 else 0
        momentum_60s = ((prices_array[-1] - prices_array[-3]) / prices_array[-3]) * 100 if len(prices_array) >= 3 else 0
        momentum_120s = ((prices_array[-1] - prices_array[-5]) / prices_array[-5]) * 100 if len(prices_array) >= 5 else 0
        
        momentum_accel = momentum_30s - momentum_120s
        
        # === VOLATILITY ===
        returns = np.diff(prices_array[-20:]) / prices_array[-20:-1]
        volatility_pct = np.std(returns) * 100
        
        vol_recent = np.std(returns[-5:]) * 100 if len(returns) >= 5 else volatility_pct
        volatility_state = "expanding" if vol_recent > volatility_pct else "contracting"
        
        # === TREND ===
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
        
        # === MEAN REVERSION ===
        distance_from_sma20 = ((current - sma_20) / sma_20) * 100
        
        if abs(distance_from_sma20) > 1.5:
            mean_reversion_pressure = "high"
        elif abs(distance_from_sma20) > 0.5:
            mean_reversion_pressure = "medium"
        else:
            mean_reversion_pressure = "low"
        
        # === SCORE ===
        score = 0.0
        
        # Momentum (40%)
        if momentum_30s > 0.2:
            score += 0.4
        elif momentum_30s < -0.2:
            score -= 0.4
        
        # Acceleration (20%)
        if momentum_accel > 0.15:
            score += 0.2
        elif momentum_accel < -0.15:
            score -= 0.2
        
        # Trend (20%)
        if trend_bias == "strong_up":
            score += 0.2
        elif trend_bias == "strong_down":
            score -= 0.2
        elif trend_bias == "weak_up":
            score += 0.1
        elif trend_bias == "weak_down":
            score -= 0.1
        
        # Volatility (10%)
        if volatility_state == "expanding" and volatility_pct > 0.5:
            score += 0.1
        
        # Mean reversion (10%)
        if mean_reversion_pressure == "high":
            if distance_from_sma20 > 1.5:
                score -= 0.1
            elif distance_from_sma20 < -1.5:
                score += 0.1
        
        # === DECISION ===
        direction = "NO_TRADE"
        confidence = 0
        threshold = 0.15  # Lowered from 0.25 to generate more signals
        
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
    
    def generate_all_signals(self) -> Dict:
        """
        Generate signals for all 4 assets.
        Returns dict with BTC, ETH, SOL, XRP signals.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        all_signals = {
            "timestamp": timestamp,
            "assets": {}
        }
        
        for asset, symbol in self.ASSETS.items():
            prices = self.fetch_asset_prices(symbol)
            
            if prices and len(prices) >= 20:
                signal = self.calculate_signal(prices)
                signal["price"] = prices[-1]
            else:
                signal = {
                    "direction": "NO_TRADE",
                    "confidence": 0,
                    "price": 0,
                    "basis": {"error": "insufficient_data"}
                }
            
            all_signals["assets"][asset] = signal
        
        return all_signals
    
    def write_signals(self, signals: Dict):
        """Write all signals to disk."""
        try:
            with open(self.signals_file, 'w') as f:
                json.dump(signals, f, indent=2)
        except Exception as e:
            print(f"❌ Error writing signals: {e}")
    
    def log_signals(self, signals: Dict):
        """Log signals periodically."""
        try:
            # Log every 20th loop (once per minute)
            if self.loop_count % 20 == 0:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(signals) + '\n')
        except Exception as e:
            print(f"⚠️  Log error: {e}")
    
    def print_status(self, signals: Dict):
        """Print signal summary."""
        now = datetime.now().strftime("%H:%M:%S")
        
        print(f"\r[{now}] ", end='')
        
        for asset in ['BTC', 'ETH', 'SOL', 'XRP']:
            signal = signals["assets"].get(asset, {})
            direction = signal.get("direction", "???")
            conf = signal.get("confidence", 0)
            price = signal.get("price", 0)
            
            if direction == "UP":
                emoji = "🟢"
            elif direction == "DOWN":
                emoji = "🔴"
            else:
                emoji = "⚪"
            
            print(f"{asset}: {emoji}{direction[:4]:4s} {conf:2d}% ${price:>8,.0f}  ", end='')
        
        print(flush=True)
    
    def run_forever(self):
        """Main loop - NEVER STOPS."""
        print("🚀 Multi-asset signal engine starting...\n")
        
        last_printed = None
        
        try:
            while True:
                self.loop_count += 1
                
                # Generate all signals
                signals = self.generate_all_signals()
                
                # Write to disk
                self.write_signals(signals)
                
                # Log periodically
                self.log_signals(signals)
                
                # Print status
                self.print_status(signals)
                
                # Wait 3 seconds
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n🛑 Signal engine stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            
            # Restart
            print("♻️  Restarting in 10 seconds...")
            time.sleep(10)
            self.run_forever()


if __name__ == "__main__":
    engine = MultiAssetSignalEngine()
    engine.run_forever()
