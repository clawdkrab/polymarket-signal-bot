#!/usr/bin/env python3
"""
HEDGE FUND QUANT STRATEGY
Aggressive 15-minute trading with multiple indicators
Goal: Trade frequently, capture small edges, compound rapidly
"""
import numpy as np
from typing import List, Dict


class QuantStrategy:
    """
    Advanced multi-indicator strategy.
    Trades frequently (not waiting for extremes).
    """
    
    # AGGRESSIVE THRESHOLDS (not conservative)
    RSI_OVERSOLD = 35  # Was 18 - now much more frequent
    RSI_OVERBOUGHT = 65  # Was 72 - now much more frequent
    MIN_CONFIDENCE = 55  # Was 70 - trade more often
    
    def analyze(self, prices: List[float]) -> Dict:
        """
        Multi-factor analysis combining:
        1. RSI (momentum)
        2. Rate of Change (velocity)
        3. Volatility (regime detection)
        4. Trend (directional bias)
        5. Recent price action (microstructure)
        6. Volume patterns (if available)
        """
        if len(prices) < 20:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        prices_array = np.array(prices)
        
        # === 1. RSI (14-period) ===
        rsi = self._calculate_rsi(prices_array, period=14)
        rsi_score = self._score_rsi(rsi)
        
        # === 2. Rate of Change ===
        roc_1 = (prices_array[-1] - prices_array[-2]) / prices_array[-2] * 100
        roc_3 = (prices_array[-1] - prices_array[-4]) / prices_array[-4] * 100
        roc_score = self._score_roc(roc_1, roc_3)
        
        # === 3. Volatility Regime ===
        volatility = np.std(np.diff(prices_array[-20:]) / prices_array[-20:-1]) * 100
        vol_score = self._score_volatility(volatility)
        
        # === 4. Trend Detection ===
        sma_short = np.mean(prices_array[-5:])
        sma_long = np.mean(prices_array[-15:])
        trend_score = self._score_trend(prices_array[-1], sma_short, sma_long)
        
        # === 5. Recent Price Action (last 3 candles) ===
        recent_changes = np.diff(prices_array[-4:])
        momentum_score = self._score_momentum(recent_changes)
        
        # === 6. Mean Reversion ===
        bb_position = self._bollinger_position(prices_array)
        mr_score = self._score_mean_reversion(bb_position)
        
        # === COMBINE SCORES ===
        total_score = (
            rsi_score * 0.25 +
            roc_score * 0.20 +
            trend_score * 0.20 +
            momentum_score * 0.15 +
            mr_score * 0.15 +
            vol_score * 0.05
        )
        
        # Determine signal
        if total_score > 0.15:  # Bullish
            signal = 'UP'
            confidence = min(95, 55 + (total_score * 100))
        elif total_score < -0.15:  # Bearish
            signal = 'DOWN'
            confidence = min(95, 55 + (abs(total_score) * 100))
        else:
            signal = 'NEUTRAL'
            confidence = 0
        
        return {
            'signal': signal,
            'confidence': int(confidence),
            'rsi': rsi,
            'momentum': roc_1,
            'volatility': volatility,
            'total_score': total_score,
            'components': {
                'rsi_score': rsi_score,
                'roc_score': roc_score,
                'trend_score': trend_score,
                'momentum_score': momentum_score,
                'mr_score': mr_score
            }
        }
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _score_rsi(self, rsi: float) -> float:
        """
        Score RSI: 
        < 35 = bullish (oversold)
        > 65 = bearish (overbought)
        """
        if rsi < 35:
            return (35 - rsi) / 35  # 0 to 1
        elif rsi > 65:
            return -(rsi - 65) / 35  # 0 to -1
        else:
            return 0
    
    def _score_roc(self, roc_1: float, roc_3: float) -> float:
        """Score rate of change (momentum)."""
        # Recent momentum
        score = 0
        
        if roc_1 > 0.5:  # Strong up move
            score += 0.5
        elif roc_1 < -0.5:  # Strong down move
            score -= 0.5
        
        if roc_3 > 1.0:  # Sustained up trend
            score += 0.5
        elif roc_3 < -1.0:  # Sustained down trend
            score -= 0.5
        
        return np.clip(score, -1, 1)
    
    def _score_volatility(self, vol: float) -> float:
        """
        High volatility = more opportunity
        But also more risk
        """
        if vol > 2.0:  # High vol
            return 0.3
        elif vol < 0.5:  # Low vol (avoid)
            return -0.5
        else:
            return 0
    
    def _score_trend(self, price: float, sma_short: float, sma_long: float) -> float:
        """Trend following score."""
        if price > sma_short > sma_long:  # Strong uptrend
            return 1.0
        elif price < sma_short < sma_long:  # Strong downtrend
            return -1.0
        elif price > sma_short:  # Weak uptrend
            return 0.5
        elif price < sma_short:  # Weak downtrend
            return -0.5
        else:
            return 0
    
    def _score_momentum(self, recent_changes: np.ndarray) -> float:
        """Score recent price momentum."""
        positive = np.sum(recent_changes > 0)
        negative = np.sum(recent_changes < 0)
        
        if positive > negative:
            return positive / len(recent_changes)
        else:
            return -negative / len(recent_changes)
    
    def _bollinger_position(self, prices: np.ndarray, period: int = 20) -> float:
        """
        Calculate position within Bollinger Bands.
        Returns: -1 (lower band) to +1 (upper band)
        """
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        
        current = prices[-1]
        
        if upper == lower:
            return 0
        
        # Normalize to -1 to +1
        position = (current - sma) / (upper - sma)
        return np.clip(position, -1, 1)
    
    def _score_mean_reversion(self, bb_position: float) -> float:
        """
        Mean reversion: extreme positions revert to mean.
        Far from mean = opportunity
        """
        if bb_position > 0.8:  # Near upper band - expect reversion down
            return -0.7
        elif bb_position < -0.8:  # Near lower band - expect reversion up
            return 0.7
        else:
            return 0


def test_strategy():
    """Test the strategy with sample data."""
    strategy = QuantStrategy()
    
    # Simulate some price data
    prices = [
        88500, 88520, 88480, 88460, 88440,
        88420, 88450, 88470, 88490, 88510,
        88530, 88520, 88500, 88480, 88470,
        88460, 88480, 88500, 88520, 88540
    ]
    
    result = strategy.analyze(prices)
    
    print("=" * 60)
    print("QUANT STRATEGY TEST")
    print("=" * 60)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"RSI: {result['rsi']:.1f}")
    print(f"Momentum: {result['momentum']:+.2f}%")
    print(f"Total Score: {result['total_score']:+.3f}")
    print()
    print("Component Scores:")
    for key, val in result['components'].items():
        print(f"  {key}: {val:+.3f}")
    print("=" * 60)


if __name__ == "__main__":
    test_strategy()
