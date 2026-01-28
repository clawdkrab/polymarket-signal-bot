# HIGH-POWERED POLYMARKET SIGNAL BOT

## Overview

Aggressive 15-minute signal generation bot for Polymarket crypto markets (BTC/ETH/SOL/XRP).

**Built for:**
- Real-time WebSocket price streaming (Binance)
- High-frequency signal updates (every 10 minutes + finalize times)
- Always-on operation (24/7 daemon)
- Instant readiness for market opens (:00, :15, :30, :45)

**NO TRADING EXECUTION** - Signals only. You trade manually on Polymarket.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install websockets requests numpy
```

### 2. Run the Bot
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
python3 signal_bot.py
```

### 3. Watch Console Output
Signals emit every 10 minutes + at finalize times (:14:50, :29:50, :44:50, :59:50)

---

## Output Files

Bot writes to 3 files (auto-created):

| File | Purpose |
|------|---------|
| `latest_signals.json` | Always current (overwritten) |
| `signals.jsonl` | Full history (append-only) |
| `readiness_snapshots.jsonl` | Only finalized signals before market opens |

---

## Console Output Example

```
[18:20:00] 📊 SIGNALS (Next Open: 18:30)
🟢 BTC  UP       74% READY@18:29:52     mom30=+0.22% mom60=+0.18% slope=+0.08 vol=exp vwap=+0.3% z=+1.2σ
🔴 ETH  DOWN     68%                    mom30=-0.15% mom60=-0.22% slope=-0.12 vol=exp vwap=-0.4% z=-0.9σ
🟢 SOL  UP       63%                    mom30=+0.11% mom60=+0.09% slope=+0.05 vol=con vwap=+0.1% z=+0.5σ
⚪ XRP  NO_TRADE 0%                     mom30=+0.02% mom60=-0.01% slope=+0.01 vol=con vwap=+0.0% z=+0.1σ


[18:29:50] 🎯 FINALIZED (Next Open: 18:30)
🟢 BTC  UP       76% READY@18:29:50     mom30=+0.24% mom60=+0.20% slope=+0.10 vol=exp vwap=+0.4% z=+1.4σ
🔴 ETH  DOWN     72% READY@18:29:50     mom30=-0.18% mom60=-0.26% slope=-0.14 vol=exp vwap=-0.5% z=-1.1σ
🟢 SOL  UP       65% READY@18:29:50     mom30=+0.13% mom60=+0.11% slope=+0.06 vol=exp vwap=+0.2% z=+0.7σ
⚪ XRP  NO_TRADE 45%                    mom30=+0.03% mom60=+0.01% slope=+0.02 vol=con vwap=+0.1% z=+0.2σ
```

---

## Signal Fields Explained

### Console Format
```
🟢 BTC  UP       74% READY@18:29:50     reasoning...
│  │    │        │   │
│  │    │        │   └─ Ready indicator (appears when confidence >= 60% and market open is <70s away)
│  │    │        └───── Confidence (0-100%)
│  │    └────────────── Direction (UP/DOWN/NO_TRADE)
│  └─────────────────── Token
└────────────────────── Emoji (🟢 UP, 🔴 DOWN, ⚪ NO_TRADE)
```

### Reasoning String
```
mom30=+0.22%    → 30-second momentum
mom60=+0.18%    → 60-second momentum
slope=+0.08     → Momentum acceleration
vol=exp         → Volatility regime (exp=expanding, con=contracting)
vwap=+0.3%      → Distance from VWAP
z=+1.2σ         → Z-score vs 2-minute mean
```

### JSON Format (`latest_signals.json`)
```json
[
  {
    "token": "BTC",
    "direction": "UP",
    "confidence": 76,
    "entry_window": "18:30–18:45",
    "reasoning": "mom30=+0.24% mom60=+0.20% slope=+0.10 vol=exp vwap=+0.4% z=+1.4σ",
    "ready": true,
    "next_open": "2026-01-28T18:30:00+00:00",
    "timestamp": "2026-01-28T18:29:50.123456+00:00",
    "type": "finalize",
    "basis": {
      "mom_15s": 0.185,
      "mom_30s": 0.240,
      "mom_60s": 0.200,
      "mom_120s": 0.175,
      "mom_slope": 0.100,
      "vol_pct": 0.450,
      "vol_regime": "expanding",
      "vwap_dist": 0.400,
      "zscore": 1.40,
      "vol_impulse": 15.3,
      "score": 0.650
    }
  }
]
```

---

## Signal Logic

### Indicators (Short-Horizon, 15m Optimized)

**Primary:**
1. **Micro-momentum** (15s, 30s, 60s, 120s) - Price velocity at multiple timeframes
2. **Momentum slope** - Is momentum accelerating or decelerating?
3. **Volatility regime** - Expanding (more conviction) vs contracting (chop)
4. **VWAP distance** - Stretch from volume-weighted average
5. **Volume impulse** - Current volume vs recent baseline

**Secondary:**
- Z-score vs 2-minute rolling mean (overextension detection)

### Scoring System

```
Score range: -1.0 (strong DOWN) to +1.0 (strong UP)

Weights:
- Micro-momentum: 40%
- Momentum acceleration: 25%
- Volatility regime: 15%
- VWAP stretch: 10%
- Volume impulse: 10%

Thresholds:
- score > +0.15  → UP
- score < -0.15  → DOWN
- else           → Attempt to pick direction from 60s momentum
                    (NO_TRADE only if truly flat)
```

### Aggressive Behavior

- **Bias toward action:** Will call UP/DOWN even on moderate signals
- **Low NO_TRADE rate:** Only used when market is genuinely flat
- **Short-term focus:** Optimized for 15-minute binary outcomes
- **High update frequency:** Always hunting for directional edge

---

## Timing

### Regular Emissions (Every 10 Minutes)
- Signals emit at :00, :10, :20, :30, :40, :50
- Type: `regular`
- Written to: `latest_signals.json` + `signals.jsonl`

### Finalized Snapshots (Before Market Opens)
- **:14:50** (for :15 market)
- **:29:50** (for :30 market)
- **:44:50** (for :45 market)
- **:59:50** (for :00 market)

- Type: `finalize`
- Written to: `latest_signals.json` + `signals.jsonl` + `readiness_snapshots.jsonl`
- Appears with **🎯 FINALIZED** in console

### Market Open Times
Polymarket 15m markets open at:
- **:00** – :15
- **:15** – :30
- **:30** – :45
- **:45** – :00

Bot finalizes signals **10 seconds before** each open.

---

## Readiness Logic

**READY** status appears when:
1. Confidence >= 60%
2. Market open is within next 70 seconds
3. Direction is UP or DOWN (not NO_TRADE)

**Example workflow:**
```
18:29:20 → Regular signal: BTC UP 74%
18:29:50 → Finalized signal: BTC UP 76% READY@18:29:50
18:30:00 → Market opens on Polymarket
18:30:05 → You place manual trade based on finalized signal
```

---

## Running 24/7

### Foreground (Default)
```bash
python3 signal_bot.py
```

### Background (nohup)
```bash
nohup python3 signal_bot.py > signal_bot.log 2>&1 &
```

### Background (tmux)
```bash
tmux new -s signals
python3 signal_bot.py
# Press Ctrl+B then D to detach
# Reattach later: tmux attach -t signals
```

### Check if Running
```bash
ps aux | grep signal_bot.py | grep -v grep
```

### Stop
```bash
pkill -f signal_bot.py
```

---

## Monitoring

### Watch Latest Signals
```bash
watch -n 3 'cat latest_signals.json | python3 -m json.tool'
```

### Tail History
```bash
tail -f signals.jsonl
```

### View Readiness Snapshots
```bash
cat readiness_snapshots.jsonl | tail -4 | python3 -m json.tool
```

### Live Console (if running in foreground)
Just watch the terminal - signals print every 10 minutes.

---

## Configuration

Edit top of `signal_bot.py`:

```python
TOKENS = ['BTC', 'ETH', 'SOL', 'XRP']  # Which tokens to watch
CONFIDENCE_THRESHOLD = 60               # READY threshold
EMISSION_INTERVAL = 600                 # 10 minutes (seconds)
FINALIZE_TIMES = ['14:50', '29:50', '44:50', '59:50']
```

---

## Data Sources

**Primary:** Binance WebSocket (real-time trades)
- Stream: `wss://stream.binance.com:9443/stream`
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT
- Update frequency: Every trade (millisecond-level)

**Fallback:** Binance REST API (if WebSocket fails)
- Endpoint: `https://api.binance.com/api/v3/ticker/price`
- Polling: Every 10 seconds (only when WebSocket is down)
- Auto-reconnect with exponential backoff

---

## Troubleshooting

### No signals appearing
```bash
# Check if bot is running
ps aux | grep signal_bot.py

# Check log output
tail -50 signal_bot.log

# Restart
pkill -f signal_bot.py
python3 signal_bot.py
```

### WebSocket connection issues
Bot auto-reconnects with exponential backoff. If it fails repeatedly:
- Check internet connection
- Check Binance API status: https://www.binance.com/en/support/announcement
- Bot will fall back to REST polling automatically

### All signals show NO_TRADE
This is rare but possible during extremely flat markets. Wait for volatility to return.

### Confidence always low
Increase sensitivity by editing `signal_bot.py`:
```python
# Line ~480 - Lower threshold
if score > 0.10:  # Was 0.15
    direction = 'UP'
```

---

## Performance

**CPU:** ~1-2% average
**Memory:** ~50-100 MB
**Network:** ~10-50 KB/s (WebSocket)
**Disk:** ~1 MB/day (logs)

**Latency:**
- WebSocket updates: <100ms
- Signal calculation: <10ms
- Total end-to-end: <200ms

---

## Notes

### Why WebSocket?
- **Low latency:** Millisecond-level price updates
- **High frequency:** Captures micro-movements critical for 15m binaries
- **Always current:** No polling delay

### Why Aggressive?
- **15-minute windows** require fast, decisive calls
- **Binary outcomes** (up/down) don't benefit from cautious "maybe" signals
- **Manual execution** means you filter final decisions anyway

### Why These Indicators?
- **Short-horizon momentum:** Most predictive for 15m outcomes
- **Volatility regime:** Distinguishes trending from chopping markets
- **VWAP/Z-score:** Identifies stretched conditions ripe for reversion
- **Volume:** Confirms conviction behind moves

---

## Extending

### Add More Tokens
Edit `TOKENS` and `BINANCE_SYMBOLS` at top of script.

### Change Emission Frequency
Edit `EMISSION_INTERVAL` (in seconds).

### Adjust Finalize Times
Edit `FINALIZE_TIMES` (MM:SS format).

### Modify Signal Logic
Edit `generate_signal()` method in `SignalEngine` class.

---

## Support

For issues or questions:
1. Check `signal_bot.log` for errors
2. Review `latest_signals.json` for output format
3. Ensure dependencies installed: `pip install websockets requests numpy`

---

**Built for Polymarket 15m markets. Ready to hunt signals 24/7.**
