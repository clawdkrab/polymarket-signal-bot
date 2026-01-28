#!/usr/bin/env python3
"""
POLYMARKET SIGNAL BOT - REST API VERSION
Optimized for Replit (no WebSocket, pure REST polling)
"""
import json
import time
import requests
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import deque
from typing import Dict, List

# Config
TOKENS = ['BTC', 'ETH', 'SOL', 'XRP']
BINANCE_SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'SOL': 'SOLUSDT',
    'XRP': 'XRPUSDT'
}

CONFIDENCE_THRESHOLD = 60
EMISSION_INTERVAL = 600  # 10 minutes
FINALIZE_TIMES = ['14:50', '29:50', '44:50', '59:50']
POLL_INTERVAL = 1  # Poll every 1 second

OUTPUT_DIR = Path(__file__).parent
LATEST_FILE = OUTPUT_DIR / "latest_signals.json"
HISTORY_FILE = OUTPUT_DIR / "signals.jsonl"
READINESS_FILE = OUTPUT_DIR / "readiness_snapshots.jsonl"

class PriceBuffer:
    def __init__(self, maxlen=300):
        self.prices = deque(maxlen=maxlen)
        self.timestamps = deque(maxlen=maxlen)
    
    def append(self, price: float):
        self.prices.append(price)
        self.timestamps.append(time.time())
    
    def get_recent(self, seconds: int) -> List[float]:
        if not self.prices:
            return []
        cutoff = time.time() - seconds
        result = []
        for i in range(len(self.timestamps) - 1, -1, -1):
            if self.timestamps[i] < cutoff:
                break
            result.append(self.prices[i])
        return list(reversed(result))
    
    def get_all(self) -> List[float]:
        return list(self.prices)

class SignalEngine:
    def __init__(self):
        self.buffers = {token: PriceBuffer() for token in TOKENS}
        self.last_signals = {}
        self.last_emission = 0
        self.last_finalize = None
        
        print("="*80)
        print("🚀 POLYMARKET SIGNAL BOT - REST API MODE")
        print("="*80)
        print(f"Tokens: {', '.join(TOKENS)}")
        print(f"Emission: Every {EMISSION_INTERVAL//60} minutes")
        print(f"Finalize: {', '.join(FINALIZE_TIMES)}")
        print(f"Data: Binance REST API (1s polling)")
        print("="*80)
        print()
    
    def update_price(self, token: str, price: float):
        if token in self.buffers:
            self.buffers[token].append(price)
    
    def calculate_momentum(self, prices: List[float], window: int) -> float:
        if len(prices) < window + 1:
            return 0.0
        old_price = prices[-window-1]
        current_price = prices[-1]
        if old_price == 0:
            return 0.0
        return ((current_price - old_price) / old_price) * 100
    
    def calculate_momentum_slope(self, prices: List[float]) -> float:
        if len(prices) < 120:
            return 0.0
        recent_mom = self.calculate_momentum(prices[-60:], 30)
        earlier_mom = self.calculate_momentum(prices[-120:-60], 30)
        return recent_mom - earlier_mom
    
    def calculate_volatility_regime(self, prices: List[float]) -> tuple:
        if len(prices) < 60:
            return 0.0, 'unknown'
        recent = np.array(prices[-30:])
        recent_vol = np.std(recent) / np.mean(recent) * 100
        earlier = np.array(prices[-60:-30])
        earlier_vol = np.std(earlier) / np.mean(earlier) * 100
        regime = 'expanding' if recent_vol > earlier_vol else 'contracting'
        return recent_vol, regime
    
    def generate_signal(self, token: str) -> Dict:
        buffer = self.buffers[token]
        prices = buffer.get_all()
        
        if len(prices) < 120:
            return {
                'token': token,
                'direction': 'NO_TRADE',
                'confidence': 0,
                'reasoning': 'insufficient_data',
                'ready': False
            }
        
        # Calculate indicators
        mom_30s = self.calculate_momentum(prices, 30)
        mom_60s = self.calculate_momentum(prices, 60)
        mom_slope = self.calculate_momentum_slope(prices)
        vol_pct, vol_regime = self.calculate_volatility_regime(prices)
        
        # Scoring
        score = 0.0
        
        if mom_30s > 0.15:
            score += 0.4
        elif mom_30s < -0.15:
            score -= 0.4
        elif mom_30s > 0.08:
            score += 0.2
        elif mom_30s < -0.08:
            score -= 0.2
        
        if mom_slope > 0.1:
            score += 0.25
        elif mom_slope < -0.1:
            score -= 0.25
        
        if vol_regime == 'expanding' and vol_pct > 0.3:
            score += 0.15 if score > 0 else -0.15
        
        # Decision
        if score > 0.15:
            direction = 'UP'
            confidence = min(95, int(55 + (score * 100)))
        elif score < -0.15:
            direction = 'DOWN'
            confidence = min(95, int(55 + (abs(score) * 100)))
        else:
            if mom_60s > 0.05:
                direction = 'UP'
                confidence = 50
            elif mom_60s < -0.05:
                direction = 'DOWN'
                confidence = 50
            else:
                direction = 'NO_TRADE'
                confidence = 0
        
        now = datetime.now(timezone.utc)
        next_open = self.get_next_market_open(now)
        entry_window = f"{next_open.strftime('%H:%M')}–{(next_open + timedelta(minutes=15)).strftime('%H:%M')}"
        
        seconds_to_open = (next_open - now).total_seconds()
        is_ready = (confidence >= CONFIDENCE_THRESHOLD and 0 < seconds_to_open <= 70)
        
        reasoning = (
            f"mom30={mom_30s:+.2f}% mom60={mom_60s:+.2f}% "
            f"slope={mom_slope:+.2f} vol={vol_regime[:3]}"
        )
        
        return {
            'token': token,
            'direction': direction,
            'confidence': confidence,
            'entry_window': entry_window,
            'reasoning': reasoning,
            'ready': is_ready,
            'next_open': next_open.isoformat(),
            'basis': {
                'mom_30s': round(mom_30s, 3),
                'mom_60s': round(mom_60s, 3),
                'mom_slope': round(mom_slope, 3),
                'vol_pct': round(vol_pct, 3),
                'vol_regime': vol_regime,
                'score': round(score, 3)
            }
        }
    
    def get_next_market_open(self, now: datetime) -> datetime:
        minute = now.minute
        if minute < 15:
            next_min = 15
        elif minute < 30:
            next_min = 30
        elif minute < 45:
            next_min = 45
        else:
            next_min = 0
        
        if next_min == 0:
            next_open = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            next_open = now.replace(minute=next_min, second=0, microsecond=0)
        
        return next_open
    
    def should_emit(self) -> bool:
        return (time.time() - self.last_emission) >= EMISSION_INTERVAL
    
    def should_finalize(self) -> bool:
        now = datetime.now(timezone.utc)
        current_time = now.strftime('%M:%S')
        
        for finalize_time in FINALIZE_TIMES:
            target_min, target_sec = map(int, finalize_time.split(':'))
            if now.minute == target_min and abs(now.second - target_sec) <= 5:
                if self.last_finalize != now.strftime('%H:%M'):
                    return True
        return False
    
    def emit_signals(self, finalize: bool = False):
        now = datetime.now(timezone.utc)
        signals = []
        for token in TOKENS:
            signal = self.generate_signal(token)
            signal['timestamp'] = now.isoformat()
            signal['type'] = 'finalize' if finalize else 'regular'
            signals.append(signal)
        
        self.last_signals = {s['token']: s for s in signals}
        self.write_latest(signals)
        self.append_history(signals)
        
        if finalize:
            self.append_readiness(signals)
            self.last_finalize = now.strftime('%H:%M')
        
        self.print_signals(signals, finalize)
        
        if not finalize:
            self.last_emission = time.time()
    
    def write_latest(self, signals: List[Dict]):
        with open(LATEST_FILE, 'w') as f:
            json.dump(signals, f, indent=2)
    
    def append_history(self, signals: List[Dict]):
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(signals) + '\n')
    
    def append_readiness(self, signals: List[Dict]):
        with open(READINESS_FILE, 'a') as f:
            f.write(json.dumps(signals) + '\n')
    
    def print_signals(self, signals: List[Dict], finalize: bool = False):
        now = datetime.now(timezone.utc)
        next_open = self.get_next_market_open(now).strftime('%H:%M')
        signal_type = "🎯 FINALIZED" if finalize else "📊 SIGNALS"
        
        print(f"\n[{now.strftime('%H:%M:%S')}] {signal_type} (Next Open: {next_open})")
        
        for signal in signals:
            token = signal['token']
            direction = signal['direction']
            confidence = signal['confidence']
            reasoning = signal['reasoning']
            ready = signal['ready']
            
            if direction == 'UP':
                emoji = '🟢'
            elif direction == 'DOWN':
                emoji = '🔴'
            else:
                emoji = '⚪'
            
            ready_str = 'READY' if ready else ''
            if ready:
                ready_str = f" {ready_str}@{now.strftime('%H:%M:%S')}"
            
            print(f"{emoji} {token:4s} {direction:8s} {confidence:2d}%{ready_str:20s} {reasoning}")
        print()

def fetch_prices(engine: SignalEngine):
    """Fetch prices via REST API."""
    for token, symbol in BINANCE_SYMBOLS.items():
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                engine.update_price(token, price)
        except Exception as e:
            print(f"⚠️  REST error for {token}: {e}")

def main():
    engine = SignalEngine()
    
    print("🔌 Fetching prices via REST API...")
    print()
    
    # Initial price fetch
    for _ in range(5):
        fetch_prices(engine)
        time.sleep(1)
    
    print("🚀 Signal loop starting...")
    print()
    
    # Initial emission
    engine.emit_signals(finalize=False)
    
    while True:
        time.sleep(POLL_INTERVAL)
        
        # Fetch prices
        fetch_prices(engine)
        
        # Check for finalize time
        if engine.should_finalize():
            engine.emit_signals(finalize=True)
        
        # Check for regular emission
        elif engine.should_emit():
            engine.emit_signals(finalize=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Signal bot stopped by user")
