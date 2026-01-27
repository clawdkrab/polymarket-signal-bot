#!/usr/bin/env python3
"""
INSTITUTIONAL-GRADE TRADING STRATEGY
Multi-gate confirmation + confidence-tiered sizing + session awareness
"""
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timezone
import pytz


class InstitutionalStrategy:
    """
    Hedge fund level strategy with:
    1. Multi-gate confirmation (momentum decel + vol expansion + range extreme/VWAP)
    2. Confidence-tiered position sizing
    3. Session-aware thresholds
    """
    
    # Session times (UTC)
    LONDON_OPEN = 8  # 08:00 UTC
    LONDON_CLOSE = 16  # 16:00 UTC
    NY_OPEN = 13  # 13:00 UTC (08:00 EST)
    NY_CLOSE = 21  # 21:00 UTC (16:00 EST)
    
    # Volatility regime thresholds
    HIGH_VOL_THRESHOLD = 1.5  # % std dev
    
    def __init__(self):
        self.lookback = 50  # Candles for calculations
    
    def analyze(self, prices: List[float], volumes: List[float] = None) -> Dict:
        """
        Full institutional analysis with multi-gate confirmation.
        """
        if len(prices) < self.lookback:
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'Insufficient data'}
        
        prices_array = np.array(prices[-self.lookback:])
        
        # === GATE 1: Momentum Deceleration ===
        momentum_gate, momentum_direction = self._check_momentum_deceleration(prices_array)
        
        # === GATE 2: Volatility Expansion ===
        vol_gate, current_vol = self._check_volatility_expansion(prices_array)
        
        # === GATE 3: Range Extreme or VWAP Deviation ===
        range_gate, vwap_dev = self._check_range_extreme_or_vwap(prices_array, volumes)
        
        # === Session Awareness ===
        is_active_session = self._is_active_session()
        is_high_vol_regime = current_vol > self.HIGH_VOL_THRESHOLD
        
        # Adjust thresholds based on session
        if is_active_session or is_high_vol_regime:
            gates_required = 2  # Loosen: need 2 of 3 gates
        else:
            gates_required = 3  # Strict: need all 3 gates
        
        # Count passed gates
        gates_passed = sum([momentum_gate, vol_gate, range_gate])
        
        # Calculate confidence based on gate strength
        confidence = self._calculate_confidence(
            momentum_gate, vol_gate, range_gate,
            momentum_direction, vwap_dev, current_vol,
            is_active_session, is_high_vol_regime
        )
        
        # Determine signal
        if gates_passed >= gates_required and confidence >= 70:
            signal = 'UP' if momentum_direction > 0 else 'DOWN'
        else:
            signal = 'NEUTRAL'
            confidence = 0
        
        # Calculate position size based on confidence tier
        position_pct = self._tiered_position_size(confidence)
        
        return {
            'signal': signal,
            'confidence': int(confidence),
            'position_pct': position_pct,
            'gates': {
                'momentum': momentum_gate,
                'volatility': vol_gate,
                'range_vwap': range_gate,
                'passed': gates_passed,
                'required': gates_required
            },
            'metrics': {
                'volatility': current_vol,
                'vwap_deviation': vwap_dev,
                'momentum_direction': momentum_direction
            },
            'session': {
                'is_active': is_active_session,
                'is_high_vol': is_high_vol_regime
            }
        }
    
    def _check_momentum_deceleration(self, prices: np.ndarray) -> Tuple[bool, float]:
        """
        GATE 1: Momentum deceleration
        Look for momentum reversals (slowing down before reversal)
        """
        # Calculate momentum over different periods
        mom_1 = (prices[-1] - prices[-2]) / prices[-2] * 100
        mom_3 = (prices[-1] - prices[-4]) / prices[-4] * 100
        mom_5 = (prices[-1] - prices[-6]) / prices[-6] * 100
        
        # Check for deceleration (momentum weakening)
        if mom_1 > 0 and mom_3 > 0:  # Upward momentum
            # Look for deceleration (bearish divergence)
            if abs(mom_1) < abs(mom_3) < abs(mom_5):
                return True, -1  # Momentum decelerating up = potential DOWN
        elif mom_1 < 0 and mom_3 < 0:  # Downward momentum
            # Look for deceleration (bullish divergence)
            if abs(mom_1) < abs(mom_3) < abs(mom_5):
                return True, 1  # Momentum decelerating down = potential UP
        
        # Also check for fresh momentum acceleration
        if abs(mom_1) > abs(mom_3) * 1.5:  # Strong acceleration
            direction = 1 if mom_1 > 0 else -1
            return True, direction
        
        return False, 0
    
    def _check_volatility_expansion(self, prices: np.ndarray) -> Tuple[bool, float]:
        """
        GATE 2: Volatility expansion
        Volatility increasing = opportunity emerging
        """
        # Recent volatility (last 10 candles)
        recent_vol = np.std(np.diff(prices[-10:]) / prices[-10:-1]) * 100
        
        # Historical volatility (last 30 candles)
        hist_vol = np.std(np.diff(prices[-30:]) / prices[-30:-1]) * 100
        
        # Expansion if recent vol > historical vol
        if recent_vol > hist_vol * 1.2:  # 20% expansion
            return True, recent_vol
        
        return False, recent_vol
    
    def _check_range_extreme_or_vwap(self, prices: np.ndarray, volumes: List[float] = None) -> Tuple[bool, float]:
        """
        GATE 3: Price at range extreme OR VWAP deviation
        """
        current_price = prices[-1]
        
        # Method 1: Range extreme
        high_20 = np.max(prices[-20:])
        low_20 = np.min(prices[-20:])
        range_20 = high_20 - low_20
        
        if range_20 > 0:
            position_in_range = (current_price - low_20) / range_20
            
            # At extremes (top 10% or bottom 10% of range)
            if position_in_range > 0.90:  # Near top = potential SHORT
                return True, -0.9
            elif position_in_range < 0.10:  # Near bottom = potential LONG
                return True, 0.9
        
        # Method 2: VWAP deviation (if volumes available)
        if volumes and len(volumes) >= len(prices):
            vwap = self._calculate_vwap(prices, np.array(volumes[-len(prices):]))
            vwap_dev = (current_price - vwap) / vwap * 100
            
            # More than 1% deviation from VWAP
            if abs(vwap_dev) > 1.0:
                return True, vwap_dev
        else:
            # Simple moving average as proxy for VWAP
            sma_20 = np.mean(prices[-20:])
            dev = (current_price - sma_20) / sma_20 * 100
            
            if abs(dev) > 1.5:
                return True, dev
        
        return False, 0.0
    
    def _calculate_vwap(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate Volume Weighted Average Price."""
        return np.sum(prices * volumes) / np.sum(volumes)
    
    def _is_active_session(self) -> bool:
        """
        Check if current time is during London or NY session.
        """
        utc_now = datetime.now(timezone.utc)
        hour = utc_now.hour
        
        # London session: 08:00-16:00 UTC
        london_active = self.LONDON_OPEN <= hour < self.LONDON_CLOSE
        
        # NY session: 13:00-21:00 UTC
        ny_active = self.NY_OPEN <= hour < self.NY_CLOSE
        
        return london_active or ny_active
    
    def _calculate_confidence(self, momentum_gate: bool, vol_gate: bool, range_gate: bool,
                             momentum_dir: float, vwap_dev: float, volatility: float,
                             is_active_session: bool, is_high_vol: bool) -> float:
        """
        Calculate confidence score based on gate strength.
        """
        confidence = 0
        
        # Base confidence from gates
        if momentum_gate:
            confidence += 25
        if vol_gate:
            confidence += 20
        if range_gate:
            confidence += 25
        
        # Bonus for strong signals
        if abs(vwap_dev) > 2.0:  # Strong VWAP deviation
            confidence += 10
        if volatility > self.HIGH_VOL_THRESHOLD:  # High volatility
            confidence += 10
        if is_active_session:  # Active trading session
            confidence += 10
        
        return min(95, confidence)
    
    def _tiered_position_size(self, confidence: float) -> float:
        """
        Confidence-tiered position sizing:
        70-74% = 3-4%
        75-79% = 5-6%
        80%+ = 7-10%
        """
        if confidence >= 80:
            # 7-10% based on exact confidence
            return 7 + ((confidence - 80) / 20) * 3  # 7% at 80, 10% at 100
        elif confidence >= 75:
            # 5-6%
            return 5 + ((confidence - 75) / 5) * 1  # 5% at 75, 6% at 79
        elif confidence >= 70:
            # 3-4%
            return 3 + ((confidence - 70) / 5) * 1  # 3% at 70, 4% at 74
        else:
            return 0  # No trade below 70%


def test_institutional_strategy():
    """Test the institutional strategy."""
    strategy = InstitutionalStrategy()
    
    # Simulate price data with volatility expansion
    np.random.seed(42)
    base = 88500
    prices = [base]
    for i in range(50):
        change = np.random.normal(0, 50 if i < 40 else 150)  # Vol expansion after candle 40
        prices.append(prices[-1] + change)
    
    result = strategy.analyze(prices)
    
    print("=" * 70)
    print("INSTITUTIONAL STRATEGY TEST")
    print("=" * 70)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Position Size: {result['position_pct']:.1f}%")
    print()
    print("Gates:")
    for gate, passed in result['gates'].items():
        if gate in ['passed', 'required']:
            print(f"  {gate}: {passed}")
        else:
            print(f"  {gate}: {'✅ PASS' if passed else '❌ FAIL'}")
    print()
    print("Metrics:")
    for key, val in result['metrics'].items():
        print(f"  {key}: {val:.3f}")
    print()
    print("Session:")
    for key, val in result['session'].items():
        print(f"  {key}: {val}")
    print("=" * 70)


if __name__ == "__main__":
    test_institutional_strategy()
