#!/usr/bin/env python3
"""
Technical Indicators
Simple, robust indicators for BTC 15-min markets.
"""
import numpy as np
from typing import List, Dict


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).
    
    Args:
        prices: List of recent prices (oldest first)
        period: RSI period (default 14)
    
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral if not enough data
    
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gains and losses
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0  # All gains
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_sma(prices: List[float], period: int) -> float:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    
    return np.mean(prices[-period:])


def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_momentum(prices: List[float], period: int = 5) -> float:
    """
    Calculate momentum (rate of change).
    
    Returns:
        Momentum as percentage change
    """
    if len(prices) < period:
        return 0.0
    
    old_price = prices[-period]
    current_price = prices[-1]
    
    if old_price == 0:
        return 0.0
    
    return ((current_price - old_price) / old_price) * 100


def calculate_volatility(prices: List[float], period: int = 10) -> float:
    """
    Calculate volatility (standard deviation of returns).
    
    Returns:
        Volatility as percentage
    """
    if len(prices) < period + 1:
        return 0.0
    
    returns = np.diff(prices[-period-1:]) / prices[-period-1:-1]
    volatility = np.std(returns) * 100
    
    return volatility


def detect_trend(prices: List[float], short_period: int = 5, long_period: int = 20) -> Dict:
    """
    Detect trend using moving average crossover.
    
    Returns:
        {
            "trend": "UP" | "DOWN" | "SIDEWAYS",
            "strength": 0-100,
            "short_ma": float,
            "long_ma": float
        }
    """
    if len(prices) < long_period:
        return {
            "trend": "SIDEWAYS",
            "strength": 0,
            "short_ma": prices[-1] if prices else 0,
            "long_ma": prices[-1] if prices else 0
        }
    
    short_ma = calculate_sma(prices, short_period)
    long_ma = calculate_sma(prices, long_period)
    
    # Determine trend direction
    if short_ma > long_ma * 1.005:  # 0.5% threshold
        trend = "UP"
    elif short_ma < long_ma * 0.995:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"
    
    # Calculate trend strength (0-100)
    diff_pct = abs((short_ma - long_ma) / long_ma) * 100
    strength = min(diff_pct * 50, 100)  # Scale to 0-100
    
    return {
        "trend": trend,
        "strength": strength,
        "short_ma": short_ma,
        "long_ma": long_ma
    }


def analyze_price_action(prices: List[float]) -> Dict:
    """
    Comprehensive price action analysis.
    
    Returns complete technical picture for decision making.
    """
    if len(prices) < 20:
        return {
            "rsi": 50.0,
            "momentum": 0.0,
            "volatility": 0.0,
            "trend": {"trend": "SIDEWAYS", "strength": 0},
            "signal": "NEUTRAL",
            "confidence": 0
        }
    
    rsi = calculate_rsi(prices, period=14)
    momentum = calculate_momentum(prices, period=5)
    volatility = calculate_volatility(prices, period=10)
    trend = detect_trend(prices, short_period=5, long_period=20)
    
    # Generate signal based on indicators
    signal = "NEUTRAL"
    confidence = 0
    
    # Oversold conditions (potential UP)
    if rsi < 30 and momentum < 0 and trend["trend"] == "DOWN":
        signal = "UP"
        confidence = min(70 + (30 - rsi), 100)  # Higher confidence = lower RSI
    
    # Overbought conditions (potential DOWN)
    elif rsi > 70 and momentum > 0 and trend["trend"] == "UP":
        signal = "DOWN"
        confidence = min(70 + (rsi - 70), 100)  # Higher confidence = higher RSI
    
    # Strong momentum continuation
    elif abs(momentum) > 2 and trend["strength"] > 30:
        if momentum > 0 and trend["trend"] == "UP":
            signal = "UP"
            confidence = min(50 + int(momentum * 10), 100)
        elif momentum < 0 and trend["trend"] == "DOWN":
            signal = "DOWN"
            confidence = min(50 + int(abs(momentum) * 10), 100)
    
    return {
        "rsi": rsi,
        "momentum": momentum,
        "volatility": volatility,
        "trend": trend,
        "signal": signal,
        "confidence": confidence
    }
