#!/usr/bin/env python3
"""
HIGH-POWERED POLYMARKET SIGNAL BOT
Aggressive 15-minute signal generation for BTC/ETH/SOL/XRP

Produces actionable UP/DOWN signals every 10 minutes + finalized signals before market opens.
Built for speed, high frequency, and decisive calls.
"""
import json
import time
import asyncio
import websockets
import requests
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import deque
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

TOKENS = ['BTC', 'ETH', 'SOL', 'XRP']
BINANCE_SYMBOLS = {
    'BTC': 'btcusdt',
    'ETH': 'ethusdt',
    'SOL': 'solusdt',
    'XRP': 'xrpusdt'
}

CONFIDENCE_THRESHOLD = 60  # READY threshold
EMISSION_INTERVAL = 600  # 10 minutes (seconds)
FINALIZE_TIMES = ['14:50', '29:50', '44:50', '59:50']  # Market prep times

OUTPUT_DIR = Path(__file__).parent
LATEST_FILE = OUTPUT_DIR / "latest_signals.json"
HISTORY_FILE = OUTPUT_DIR / "signals.jsonl"
READINESS_FILE = OUTPUT_DIR / "readiness_snapshots.jsonl"

WEBSOCKET_URL = "wss://stream.binance.com:9443/stream?streams="

# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class PriceBuffer:
    """Ring buffer for price data with time-windowed access."""
    
    def __init__(self, maxlen=300):  # 5 minutes at 1s updates
        self.prices = deque(maxlen=maxlen)
        self.timestamps = deque(maxlen=maxlen)
        self.volumes = deque(maxlen=maxlen)
    
    def append(self, price: float, volume: float = 0):
        self.prices.append(price)
        self.timestamps.append(time.time())
        self.volumes.append(volume)
    
    def get_recent(self, seconds: int) -> List[float]:
        """Get prices from last N seconds."""
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
    """
    Aggressive signal generation engine.
    Continuously analyzes price action and produces UP/DOWN calls.
    """
    
    def __init__(self):
        self.buffers = {token: PriceBuffer() for token in TOKENS}
        self.last_signals = {}
        self.last_emission = 0
        self.last_finalize = None
        
        print("="*80)
        print("🚀 POLYMARKET SIGNAL BOT - ALWAYS HUNTING")
        print("="*80)
        print(f"Tokens: {', '.join(TOKENS)}")
        print(f"Emission: Every {EMISSION_INTERVAL//60} minutes")
        print(f"Finalize: {', '.join(FINALIZE_TIMES)}")
        print(f"Threshold: {CONFIDENCE_THRESHOLD}% for READY")
        print("="*80)
        print()
    
    def update_price(self, token: str, price: float, volume: float = 0):
        """Update price buffer (called from WebSocket)."""
        if token in self.buffers:
            self.buffers[token].append(price, volume)
    
    def calculate_momentum(self, prices: List[float], window: int) -> float:
        """Calculate % return over window."""
        if len(prices) < window + 1:
            return 0.0
        
        old_price = prices[-window-1]
        current_price = prices[-1]
        
        if old_price == 0:
            return 0.0
        
        return ((current_price - old_price) / old_price) * 100
    
    def calculate_momentum_slope(self, prices: List[float]) -> float:
        """Momentum acceleration (is momentum increasing or decreasing?)."""
        if len(prices) < 120:
            return 0.0
        
        # Compare recent momentum vs earlier momentum
        recent_mom = self.calculate_momentum(prices[-60:], 30)
        earlier_mom = self.calculate_momentum(prices[-120:-60], 30)
        
        return recent_mom - earlier_mom
    
    def calculate_volatility_regime(self, prices: List[float]) -> tuple:
        """Returns (volatility_pct, 'expanding'/'contracting')."""
        if len(prices) < 60:
            return 0.0, 'unknown'
        
        # Recent volatility
        recent = np.array(prices[-30:])
        recent_vol = np.std(recent) / np.mean(recent) * 100
        
        # Earlier volatility
        earlier = np.array(prices[-60:-30])
        earlier_vol = np.std(earlier) / np.mean(earlier) * 100
        
        regime = 'expanding' if recent_vol > earlier_vol else 'contracting'
        
        return recent_vol, regime
    
    def calculate_vwap_distance(self, prices: List[float], volumes: List[float]) -> float:
        """Distance from VWAP (%)."""
        if len(prices) < 30 or sum(volumes[-30:]) == 0:
            return 0.0
        
        recent_prices = np.array(prices[-30:])
        recent_volumes = np.array(volumes[-30:])
        
        vwap = np.sum(recent_prices * recent_volumes) / np.sum(recent_volumes)
        current = prices[-1]
        
        if vwap == 0:
            return 0.0
        
        return ((current - vwap) / vwap) * 100
    
    def calculate_zscore(self, prices: List[float], window: int = 120) -> float:
        """Z-score vs rolling mean."""
        if len(prices) < window:
            return 0.0
        
        recent = np.array(prices[-window:])
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std == 0:
            return 0.0
        
        return (prices[-1] - mean) / std
    
    def calculate_volume_impulse(self, volumes: List[float]) -> float:
        """Current volume vs baseline."""
        if len(volumes) < 30:
            return 0.0
        
        recent = volumes[-10:]
        baseline = volumes[-30:-10]
        
        if len(baseline) == 0 or np.mean(baseline) == 0:
            return 0.0
        
        return (np.mean(recent) - np.mean(baseline)) / np.mean(baseline) * 100
    
    def generate_signal(self, token: str) -> Dict:
        """
        Generate signal for a token.
        This is the core logic - aggressive and opinionated.
        """
        buffer = self.buffers[token]
        prices = buffer.get_all()
        volumes = list(buffer.volumes)
        
        if len(prices) < 120:
            # Not enough data yet
            return {
                'token': token,
                'direction': 'NO_TRADE',
                'confidence': 0,
                'reasoning': 'insufficient_data',
                'ready': False
            }
        
        # === CALCULATE INDICATORS ===
        
        # Micro-momentum at multiple horizons
        mom_15s = self.calculate_momentum(prices, 15)
        mom_30s = self.calculate_momentum(prices, 30)
        mom_60s = self.calculate_momentum(prices, 60)
        mom_120s = self.calculate_momentum(prices, 120)
        
        # Momentum acceleration
        mom_slope = self.calculate_momentum_slope(prices)
        
        # Volatility regime
        vol_pct, vol_regime = self.calculate_volatility_regime(prices)
        
        # VWAP distance
        vwap_dist = self.calculate_vwap_distance(prices, volumes)
        
        # Z-score
        zscore = self.calculate_zscore(prices)
        
        # Volume impulse
        vol_impulse = self.calculate_volume_impulse(volumes)
        
        # === SCORING SYSTEM ===
        score = 0.0
        
        # 1. Micro-momentum (40% weight)
        # Strong recent momentum
        if mom_30s > 0.15:
            score += 0.4
        elif mom_30s < -0.15:
            score -= 0.4
        elif mom_30s > 0.08:
            score += 0.2
        elif mom_30s < -0.08:
            score -= 0.2
        
        # 2. Momentum acceleration (25% weight)
        # Is momentum building or fading?
        if mom_slope > 0.1:
            score += 0.25
        elif mom_slope < -0.1:
            score -= 0.25
        elif mom_slope > 0.05:
            score += 0.1
        elif mom_slope < -0.05:
            score -= 0.1
        
        # 3. Volatility regime (15% weight)
        # Expanding volatility = more conviction
        if vol_regime == 'expanding' and vol_pct > 0.3:
            score += 0.15 if score > 0 else -0.15
        
        # 4. VWAP stretch (10% weight)
        # Extreme stretch = mean reversion bias
        if abs(vwap_dist) > 0.5:
            if vwap_dist > 0.5:
                score -= 0.1  # Overextended, fade
            elif vwap_dist < -0.5:
                score += 0.1  # Underextended, buy
        
        # 5. Volume impulse (10% weight)
        if vol_impulse > 20:
            score += 0.1 if score > 0 else -0.1
        
        # === DECISION ===
        # AGGRESSIVE: Low threshold for directional calls
        if score > 0.15:
            direction = 'UP'
            confidence = min(95, int(55 + (score * 100)))
        elif score < -0.15:
            direction = 'DOWN'
            confidence = min(95, int(55 + (abs(score) * 100)))
        else:
            # Still try to pick a direction if possible
            if mom_60s > 0.05:
                direction = 'UP'
                confidence = 50
            elif mom_60s < -0.05:
                direction = 'DOWN'
                confidence = 50
            else:
                direction = 'NO_TRADE'
                confidence = 0
        
        # === NEXT MARKET WINDOW ===
        now = datetime.now(timezone.utc)
        next_open = self.get_next_market_open(now)
        entry_window = f"{next_open.strftime('%H:%M')}–{(next_open + timedelta(minutes=15)).strftime('%H:%M')}"
        
        # === READINESS ===
        # Check if we're within 70 seconds of market open
        seconds_to_open = (next_open - now).total_seconds()
        is_ready = (confidence >= CONFIDENCE_THRESHOLD and 0 < seconds_to_open <= 70)
        
        # === REASONING ===
        reasoning = (
            f"mom30={mom_30s:+.2f}% mom60={mom_60s:+.2f}% "
            f"slope={mom_slope:+.2f} vol={vol_regime[:3]} "
            f"vwap={vwap_dist:+.1f}% z={zscore:+.1f}σ"
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
                'mom_15s': round(mom_15s, 3),
                'mom_30s': round(mom_30s, 3),
                'mom_60s': round(mom_60s, 3),
                'mom_120s': round(mom_120s, 3),
                'mom_slope': round(mom_slope, 3),
                'vol_pct': round(vol_pct, 3),
                'vol_regime': vol_regime,
                'vwap_dist': round(vwap_dist, 3),
                'zscore': round(zscore, 2),
                'vol_impulse': round(vol_impulse, 1),
                'score': round(score, 3)
            }
        }
    
    def get_next_market_open(self, now: datetime) -> datetime:
        """Calculate next market open time (00, 15, 30, 45)."""
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
        """Check if it's time for regular emission (every 10 minutes)."""
        return (time.time() - self.last_emission) >= EMISSION_INTERVAL
    
    def should_finalize(self) -> bool:
        """Check if we're at a finalize timestamp (:14:50, :29:50, etc)."""
        now = datetime.now(timezone.utc)
        current_time = now.strftime('%M:%S')
        
        # Check if we're within 5 seconds of any finalize time
        for finalize_time in FINALIZE_TIMES:
            target_min, target_sec = map(int, finalize_time.split(':'))
            
            if now.minute == target_min and abs(now.second - target_sec) <= 5:
                # Prevent duplicate finalizations
                if self.last_finalize != now.strftime('%H:%M'):
                    return True
        
        return False
    
    def emit_signals(self, finalize: bool = False):
        """Generate and output signal set for all tokens."""
        now = datetime.now(timezone.utc)
        
        signals = []
        for token in TOKENS:
            signal = self.generate_signal(token)
            signal['timestamp'] = now.isoformat()
            signal['type'] = 'finalize' if finalize else 'regular'
            signals.append(signal)
        
        # Update last signals
        self.last_signals = {s['token']: s for s in signals}
        
        # Write to disk
        self.write_latest(signals)
        self.append_history(signals)
        
        if finalize:
            self.append_readiness(signals)
            self.last_finalize = now.strftime('%H:%M')
        
        # Print to console
        self.print_signals(signals, finalize)
        
        # Update emission time
        if not finalize:
            self.last_emission = time.time()
    
    def write_latest(self, signals: List[Dict]):
        """Overwrite latest_signals.json."""
        with open(LATEST_FILE, 'w') as f:
            json.dump(signals, f, indent=2)
    
    def append_history(self, signals: List[Dict]):
        """Append to signals.jsonl."""
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(signals) + '\n')
    
    def append_readiness(self, signals: List[Dict]):
        """Append to readiness_snapshots.jsonl."""
        with open(READINESS_FILE, 'a') as f:
            f.write(json.dumps(signals) + '\n')
    
    def print_signals(self, signals: List[Dict], finalize: bool = False):
        """Print signals to console."""
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
            
            # Direction emoji
            if direction == 'UP':
                emoji = '🟢'
            elif direction == 'DOWN':
                emoji = '🔴'
            else:
                emoji = '⚪'
            
            # Ready indicator
            ready_str = 'READY' if ready else ''
            if ready:
                ready_str = f" {ready_str}@{now.strftime('%H:%M:%S')}"
            
            print(f"{emoji} {token:4s} {direction:8s} {confidence:2d}%{ready_str:20s} {reasoning}")
        
        print()


# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET PRICE FEED
# ═══════════════════════════════════════════════════════════════════════════

async def price_feed(engine: SignalEngine):
    """
    Connect to Binance WebSocket and stream prices.
    Updates engine buffers in real-time.
    """
    # Build stream URL
    streams = [f"{symbol}@trade" for symbol in BINANCE_SYMBOLS.values()]
    url = WEBSOCKET_URL + "/".join(streams)
    
    print(f"🔌 Connecting to Binance WebSocket...")
    print(f"   Streams: {', '.join(TOKENS)}")
    print()
    
    reconnect_delay = 1
    
    while True:
        try:
            async with websockets.connect(url) as ws:
                print(f"✅ WebSocket connected")
                reconnect_delay = 1  # Reset on successful connection
                
                async for message in ws:
                    data = json.loads(message)
                    
                    # Parse trade data
                    if 'data' in data:
                        trade = data['data']
                        symbol = trade['s'].upper()
                        price = float(trade['p'])
                        volume = float(trade['q'])
                        
                        # Map to token
                        for token, binance_symbol in BINANCE_SYMBOLS.items():
                            if symbol == binance_symbol.upper():
                                engine.update_price(token, price, volume)
                                break
        
        except Exception as e:
            print(f"⚠️  WebSocket error: {e}")
            print(f"   Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff


async def signal_loop(engine: SignalEngine):
    """
    Main signal generation loop.
    Emits signals every 10 minutes + at finalize times.
    """
    # Wait a bit for initial price data
    await asyncio.sleep(5)
    
    print("🚀 Signal loop starting...")
    print()
    
    # Initial emission
    engine.emit_signals(finalize=False)
    
    while True:
        await asyncio.sleep(1)  # Check every second
        
        # Check for finalize time
        if engine.should_finalize():
            engine.emit_signals(finalize=True)
        
        # Check for regular emission
        elif engine.should_emit():
            engine.emit_signals(finalize=False)


async def rest_fallback(engine: SignalEngine):
    """
    Fallback: Fetch prices via REST if WebSocket fails.
    Only runs if no price updates in last 10 seconds.
    """
    await asyncio.sleep(60)  # Initial delay
    
    while True:
        await asyncio.sleep(10)
        
        # Check if we have recent data
        now = time.time()
        needs_fallback = False
        
        for token in TOKENS:
            buffer = engine.buffers[token]
            if not buffer.timestamps or (now - buffer.timestamps[-1]) > 10:
                needs_fallback = True
                break
        
        if needs_fallback:
            print("⚠️  Using REST fallback for price data")
            
            for token, symbol in BINANCE_SYMBOLS.items():
                try:
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        price = float(data['price'])
                        engine.update_price(token, price, 0)
                
                except Exception as e:
                    print(f"   REST error for {token}: {e}")
            
            await asyncio.sleep(3)


async def main():
    """Main entry point."""
    engine = SignalEngine()
    
    # Run WebSocket feed, signal loop, and REST fallback concurrently
    await asyncio.gather(
        price_feed(engine),
        signal_loop(engine),
        rest_fallback(engine)
    )


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Signal bot stopped by user")
