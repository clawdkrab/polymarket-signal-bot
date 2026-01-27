#!/usr/bin/env python3
"""
Paper Trading System
Simulates BTC 15-minute markets for strategy testing without real capital.
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class SyntheticMarket:
    """Represents a synthetic BTC 15-minute Up/Down market."""
    
    def __init__(self, start_price: float, duration_minutes: int = 15):
        self.start_price = start_price
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.resolved = False
        self.end_price = None
        self.actual_outcome = None  # "UP" or "DOWN"
        
        # Generate synthetic market ID
        self.market_id = f"SYNTHETIC_BTC_{int(self.start_time.timestamp())}"
        self.question = f"Will BTC be above ${start_price:,.2f} in {duration_minutes} minutes?"
    
    def resolve(self, end_price: float):
        """Resolve the market with the actual ending price."""
        self.end_price = end_price
        self.resolved = True
        
        # Determine outcome
        if end_price > self.start_price:
            self.actual_outcome = "UP"
        else:
            self.actual_outcome = "DOWN"
        
        return self.actual_outcome
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "market_id": self.market_id,
            "question": self.question,
            "start_price": self.start_price,
            "end_price": self.end_price,
            "actual_outcome": self.actual_outcome,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "resolved": self.resolved
        }


class PaperTrade:
    """Represents a simulated trade on a synthetic market."""
    
    def __init__(
        self,
        market: SyntheticMarket,
        prediction: str,  # "UP" or "DOWN"
        position_size: float,
        confidence: int,
        entry_price: float = 0.5  # Assumed market price
    ):
        self.market = market
        self.prediction = prediction
        self.position_size = position_size
        self.confidence = confidence
        self.entry_price = entry_price
        self.shares = position_size / entry_price
        
        self.timestamp = datetime.now()
        self.resolved = False
        self.pnl = 0.0
        self.won = False
    
    def resolve(self):
        """Calculate P&L after market resolves."""
        if not self.market.resolved:
            raise ValueError("Cannot resolve trade - market not resolved yet")
        
        self.resolved = True
        
        # Did we predict correctly?
        self.won = (self.prediction == self.market.actual_outcome)
        
        if self.won:
            # Win: shares worth $1 each
            self.pnl = (1.0 - self.entry_price) * self.shares
        else:
            # Loss: shares worth $0
            self.pnl = -self.entry_price * self.shares
        
        return self.pnl
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "market_id": self.market.market_id,
            "prediction": self.prediction,
            "position_size": self.position_size,
            "shares": self.shares,
            "entry_price": self.entry_price,
            "confidence": self.confidence,
            "resolved": self.resolved,
            "won": self.won,
            "pnl": self.pnl,
            "actual_outcome": self.market.actual_outcome if self.market.resolved else None
        }


class PaperTradingEngine:
    """Manages paper trading simulation."""
    
    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        self.active_markets: List[SyntheticMarket] = []
        self.resolved_markets: List[SyntheticMarket] = []
        
        self.active_trades: List[PaperTrade] = []
        self.resolved_trades: List[PaperTrade] = []
        
        # Performance tracking
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        
        # Memory
        memory_dir = Path(__file__).parent.parent / "memory"
        memory_dir.mkdir(exist_ok=True)
        self.paper_log = memory_dir / "paper_trades.jsonl"
        self.paper_state = memory_dir / "paper_state.json"
        
        # Load previous state
        self._load_state()
    
    def _load_state(self):
        """Load previous paper trading state."""
        if self.paper_state.exists():
            with open(self.paper_state) as f:
                state = json.load(f)
                self.capital = state.get("capital", self.initial_capital)
                self.total_trades = state.get("total_trades", 0)
                self.wins = state.get("wins", 0)
                self.losses = state.get("losses", 0)
                self.total_pnl = state.get("total_pnl", 0.0)
    
    def _save_state(self):
        """Save current paper trading state."""
        state = {
            "capital": self.capital,
            "initial_capital": self.initial_capital,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "total_pnl": self.total_pnl,
            "win_rate": (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0,
            "roi": ((self.capital - self.initial_capital) / self.initial_capital * 100),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.paper_state, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _log_trade(self, trade: PaperTrade):
        """Log trade to JSONL."""
        with open(self.paper_log, 'a') as f:
            f.write(json.dumps(trade.to_dict()) + '\n')
    
    def create_market(self, current_price: float, duration_minutes: int = 15) -> SyntheticMarket:
        """Create a new synthetic market."""
        market = SyntheticMarket(current_price, duration_minutes)
        self.active_markets.append(market)
        return market
    
    def place_trade(
        self,
        market: SyntheticMarket,
        prediction: str,
        position_size: float,
        confidence: int
    ) -> PaperTrade:
        """Place a paper trade on a synthetic market."""
        # Deduct capital
        if position_size > self.capital:
            raise ValueError(f"Insufficient capital: ${self.capital:.2f} < ${position_size:.2f}")
        
        self.capital -= position_size
        
        # Create trade
        trade = PaperTrade(market, prediction, position_size, confidence)
        self.active_trades.append(trade)
        self.total_trades += 1
        
        return trade
    
    def resolve_market(self, market: SyntheticMarket, end_price: float):
        """Resolve a market and all trades on it."""
        # Resolve the market
        outcome = market.resolve(end_price)
        
        # Move to resolved
        if market in self.active_markets:
            self.active_markets.remove(market)
        self.resolved_markets.append(market)
        
        # Resolve all trades on this market
        for trade in self.active_trades[:]:
            if trade.market.market_id == market.market_id:
                pnl = trade.resolve()
                
                # Update capital
                self.capital += trade.position_size + pnl
                
                # Update stats
                self.total_pnl += pnl
                if trade.won:
                    self.wins += 1
                else:
                    self.losses += 1
                
                # Move to resolved
                self.active_trades.remove(trade)
                self.resolved_trades.append(trade)
                
                # Log trade
                self._log_trade(trade)
        
        # Save state
        self._save_state()
        
        return outcome
    
    def get_performance(self) -> dict:
        """Get current performance metrics."""
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        roi = ((self.capital - self.initial_capital) / self.initial_capital * 100)
        
        return {
            "capital": self.capital,
            "initial_capital": self.initial_capital,
            "total_pnl": self.total_pnl,
            "roi": roi,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": win_rate,
            "active_markets": len(self.active_markets),
            "active_trades": len(self.active_trades)
        }
