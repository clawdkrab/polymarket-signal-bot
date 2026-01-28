# Polymarket BTC Agent

High-powered signal bot for Polymarket 15-minute crypto markets (BTC/ETH/SOL/XRP).

## Features

- ✅ **Real-time WebSocket** - Binance price streams (millisecond updates)
- ✅ **Micro-momentum analysis** - 15s/30s/60s/120s horizons
- ✅ **Aggressive signals** - Bias toward actionable UP/DOWN calls
- ✅ **Pre-market ready** - Signals finalized 10 seconds before market opens
- ✅ **24/7 operation** - Always hunting for trading opportunities
- ✅ **Signal-only** - No trading execution (you trade manually)

## Quick Start

### Local

```bash
# Install dependencies
pip install -r requirements.txt

# Run the signal bot
python3 signal_bot.py
```

### Replit (24/7 hosting)

1. Import this repo to Replit
2. Click "Run"
3. Bot starts automatically and runs forever

## Output Files

- `latest_signals.json` - Current signals (always up-to-date)
- `signals.jsonl` - Full history (append-only)
- `readiness_snapshots.jsonl` - Finalized signals before market opens

## Signal Schedule

**Regular emissions:** Every 10 minutes  
**Finalized signals:** :14:50, :29:50, :44:50, :59:50 (before market opens)

Markets open at: **:00, :15, :30, :45**

## Console Output Example

```
[19:44:50] 🎯 FINALIZED (Next Open: 19:45)
🟢 BTC  UP       78% READY@19:44:50     mom30=+0.24% mom60=+0.18% slope=+0.08 vol=exp vwap=+0.3% z=+1.2σ
🔴 ETH  DOWN     72% READY@19:44:50     mom30=-0.18% mom60=-0.26% slope=-0.12 vol=exp vwap=-0.4% z=-0.9σ
🟢 SOL  UP       65% READY@19:44:50     mom30=+0.13% mom60=+0.11% slope=+0.05 vol=exp vwap=+0.1% z=+0.7σ
⚪ XRP  NO_TRADE 45%                    mom30=+0.03% mom60=-0.01% slope=+0.02 vol=con vwap=+0.0% z=+0.1σ
```

## Trading Workflow

1. Bot finalizes signals 10 seconds before market opens
2. Check `latest_signals.json` for READY signals
3. Trade signals with confidence >= 70% on Polymarket
4. Open https://polymarket.com/crypto/15M
5. Execute trades manually based on signals

## Configuration

Edit top of `signal_bot.py`:

```python
TOKENS = ['BTC', 'ETH', 'SOL', 'XRP']  # Tokens to watch
CONFIDENCE_THRESHOLD = 60               # READY threshold
EMISSION_INTERVAL = 600                 # 10 minutes
FINALIZE_TIMES = ['14:50', '29:50', '44:50', '59:50']
```

## Documentation

- **SIGNAL_BOT_README.md** - Complete guide (signal interpretation, timing, troubleshooting)
- **MANUAL_TRADING.md** - Manual trading workflow
- **AUTONOMOUS_SYSTEM.md** - Autonomous execution (advanced)

## Components

### Signal Bot (Production)
- **signal_bot.py** - Main signal engine (USE THIS)
- Real-time WebSocket + micro-momentum
- Built for Polymarket 15m cadence

### Autonomous Trading (Optional)
- **autonomous_trade_executor.py** - Auto-execution via Playwright
- **continuous_signal_engine.py** - Legacy signal engine
- **supervisor.sh** - Process manager

## Monitoring

```bash
# Watch live console output
tail -f signal_bot.log

# View current signals
cat latest_signals.json | python3 -m json.tool

# Monitor finalized signals
tail readiness_snapshots.jsonl | python3 -m json.tool
```

## Tech Stack

- Python 3.9+
- WebSockets (Binance real-time streams)
- NumPy (technical analysis)
- Requests (REST fallback)

## License

MIT

## Disclaimer

This is a signal generation tool only. No trading execution. Use at your own risk.
