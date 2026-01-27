#!/usr/bin/env python3
"""
Risk Management & Position Sizing
Dynamic position sizing based on confidence, capital, and recent performance.
"""
from typing import Dict


class RiskManager:
    """Manages position sizing and risk parameters."""
    
    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = initial_capital
        self.max_position_pct = 0.15  # Max 15% of capital per trade
        self.base_position_pct = 0.05  # Base position is 5%
        self.min_position = 1.0  # Minimum $1 position
        
        # Risk limits
        self.max_daily_loss_pct = 0.20  # Stop if down 20% in a day
        self.max_drawdown_pct = 0.25  # Reduce size if down 25% from peak
        
        # Performance tracking for adaptive sizing
        self.recent_trades = []
        self.peak_capital = initial_capital
    
    def calculate_position_size(
        self,
        capital: float,
        confidence: int,
        recent_pnl: float = 0.0,
        win_streak: int = 0,
        loss_streak: int = 0
    ) -> float:
        """
        Calculate position size based on multiple factors.
        
        Args:
            capital: Current capital
            confidence: Signal confidence (0-100)
            recent_pnl: P&L from recent trades
            win_streak: Number of consecutive wins
            loss_streak: Number of consecutive losses
        
        Returns:
            Position size in dollars
        """
        # Base position from confidence
        confidence_multiplier = confidence / 100.0
        base_size = capital * self.base_position_pct * confidence_multiplier
        
        # Adjust for recent performance
        if loss_streak >= 2:
            # Reduce size after losses
            base_size *= 0.5
        elif win_streak >= 2:
            # Slightly increase after wins (but capped)
            base_size *= 1.2
        
        # Drawdown protection
        drawdown = (self.peak_capital - capital) / self.peak_capital
        if drawdown > 0.10:  # Down more than 10%
            base_size *= 0.7  # Reduce to 70%
        if drawdown > 0.20:  # Down more than 20%
            base_size *= 0.5  # Reduce to 50%
        
        # Apply limits
        max_size = capital * self.max_position_pct
        position_size = max(self.min_position, min(base_size, max_size))
        
        # Never risk more than we have
        position_size = min(position_size, capital * 0.95)  # Keep 5% buffer
        
        return round(position_size, 2)
    
    def should_trade(
        self,
        capital: float,
        confidence: int,
        daily_pnl: float = 0.0
    ) -> tuple[bool, str]:
        """
        Determine if we should trade given current conditions.
        
        Returns:
            (should_trade: bool, reason: str)
        """
        # Check minimum confidence threshold
        if confidence < 60:
            return False, f"Confidence too low ({confidence}% < 60%)"
        
        # Check capital preservation
        if capital < self.initial_capital * 0.30:  # Down to 30% of starting
            return False, f"Capital preservation mode (${capital:.2f} < ${self.initial_capital * 0.30:.2f})"
        
        # Check daily loss limit
        daily_loss_pct = abs(daily_pnl) / self.initial_capital
        if daily_pnl < 0 and daily_loss_pct > self.max_daily_loss_pct:
            return False, f"Daily loss limit hit ({daily_loss_pct:.1%} > {self.max_daily_loss_pct:.1%})"
        
        # Check drawdown
        drawdown = (self.peak_capital - capital) / self.peak_capital
        if drawdown > self.max_drawdown_pct:
            return False, f"Max drawdown exceeded ({drawdown:.1%} > {self.max_drawdown_pct:.1%})"
        
        return True, "All risk checks passed"
    
    def update_peak(self, capital: float):
        """Update peak capital for drawdown tracking."""
        if capital > self.peak_capital:
            self.peak_capital = capital
    
    def get_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion fraction.
        
        Returns optimal bet size as fraction of capital.
        """
        if win_rate == 0 or avg_loss == 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Use fractional Kelly (25%) for safety
        return max(0, kelly * 0.25)
