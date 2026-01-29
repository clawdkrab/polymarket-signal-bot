# POLYMARKET AUTONOMOUS TRADING SYSTEM

Full autonomous pipeline: signal generation → trade execution → profit.

## Architecture

**Signal Bot** (`signal_bot_rest.py`)
- Polls Binance REST API every second
- Generates UP/DOWN signals every 10 minutes
- Finalizes signals 10 seconds before market opens
- Outputs to `latest_signals.json`

**Autonomous Executor** (`autonomous_executor.py`)
- Monitors `latest_signals.json`
- Executes trades automatically when signals are READY
- Uses Playwright to control Polymarket browser
- Logs all trades to `auto_trades.jsonl`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Trading Parameters

Edit `autonomous_executor.py`:

```python
MIN_CONFIDENCE = 70    # Only trade signals >= 70%
POSITION_SIZE = 10     # USD per trade
MAX_TRADES_PER_MARKET = 1  # Prevent duplicate trades
```

### 3. Login to Polymarket

Open https://polymarket.com and login with your wallet.
Keep the browser session alive.

### 4. Run the System

**Option A: Supervisor Script (Recommended)**
```bash
./run_autonomous.sh
```

**Option B: Manual (two terminals)**

Terminal 1:
```bash
python3 signal_bot_rest.py
```

Terminal 2:
```bash
python3 autonomous_executor.py
```

## How It Works

### Signal Generation (Every 10 Minutes)

1. Bot fetches BTC/ETH/SOL/XRP prices from Binance
2. Calculates momentum, volatility, trends
3. Generates UP/DOWN/NO_TRADE signals with confidence scores
4. At :14:50, :29:50, :44:50, :59:50 → **FINALIZE** signals for next market open

### Trade Execution (When READY)

1. Executor checks `latest_signals.json` every 5 seconds
2. When signal is READY (confidence ≥ 70% AND <70s to market open):
   - Opens Polymarket 15M page
   - Finds the correct token market (BTC/ETH/SOL/XRP)
   - Clicks UP or DOWN based on signal
   - Enters position size ($10 default)
   - Confirms trade
   - Logs result to `auto_trades.jsonl`

### Example Timeline

```
19:44:30 → Signal: BTC UP 65% (not ready)
19:44:50 → FINALIZE: BTC UP 78% READY ✅
19:44:51 → Executor detects READY signal
19:44:52 → Opens Polymarket
19:44:53 → Finds BTC 15M market
19:44:54 → Clicks UP, enters $10
19:44:55 → Trade executed ✅
19:45:00 → Market opens (trade placed 5 seconds early)
```

## Safety Features

### Duplicate Prevention
- Tracks executed trades by `token_entrywindow`
- Won't trade same market twice

### Confidence Threshold
- Only trades signals ≥ 70% confidence
- Ignores NO_TRADE signals

### Position Sizing
- Fixed $10 per trade (configurable)
- No compounding (yet)

### Browser Automation
- Runs in non-headless mode (you can watch it work)
- Manual intervention possible at any time
- Logs all attempts (success + failures)

## Monitoring

### Watch Signals Live
```bash
tail -f latest_signals.json
```

### Watch Trade Execution
```bash
tail -f auto_trades.jsonl
```

### Check Signal Bot Logs
```bash
tail -f signal_bot.log
```

### View Trade History
```bash
cat auto_trades.jsonl | jq
```

## Trade Log Format

```json
{
  "timestamp": "2026-01-28T19:44:55.123456+00:00",
  "token": "BTC",
  "direction": "UP",
  "confidence": 78,
  "entry_window": "19:45–20:00",
  "position_size": 10,
  "status": "executed",
  "error": null
}
```

## Configuration Options

### Signal Bot (`signal_bot_rest.py`)

```python
TOKENS = ['BTC', 'ETH', 'SOL', 'XRP']  # Which tokens
CONFIDENCE_THRESHOLD = 60               # READY threshold
EMISSION_INTERVAL = 600                 # 10 minutes
FINALIZE_TIMES = ['14:50', '29:50', '44:50', '59:50']
POLL_INTERVAL = 1                       # Price fetch frequency
```

### Executor (`autonomous_executor.py`)

```python
MIN_CONFIDENCE = 70        # Min confidence to trade
POSITION_SIZE = 10         # USD per trade
MAX_TRADES_PER_MARKET = 1  # Trades per market window
```

## Stopping the System

**Ctrl+C** in the terminal running `run_autonomous.sh`

Or kill manually:
```bash
pkill -f signal_bot_rest.py
pkill -f autonomous_executor.py
```

## Production Deployment

### Run 24/7 (tmux)
```bash
tmux new -s polymarket
./run_autonomous.sh
# Ctrl+B then D to detach
# Reattach: tmux attach -s polymarket
```

### Run 24/7 (nohup)
```bash
nohup ./run_autonomous.sh > system.log 2>&1 &
```

### Headless Mode
Edit `autonomous_executor.py`:
```python
browser = p.chromium.launch(headless=True)
```

## Troubleshooting

### No signals appearing
```bash
# Check if signal bot is running
ps aux | grep signal_bot_rest.py

# Check logs
tail -50 signal_bot.log
```

### Trades not executing
- Ensure you're logged in to Polymarket
- Check `auto_trades.jsonl` for error messages
- Verify MIN_CONFIDENCE threshold isn't too high

### Browser crashes
- Install Playwright browsers: `playwright install chromium`
- Check system resources (RAM)

### Wrong market selected
- Market finding is based on token name matching
- Check Polymarket 15M page structure hasn't changed
- Update `find_market_on_page()` function if needed

## Risk Warnings

⚠️ **This is autonomous trading software**
- Trades execute automatically without confirmation
- Can place dozens of trades per day
- Real money at risk
- Test with small position sizes first

⚠️ **Market Risk**
- Polymarket 15M markets are volatile
- Signals are not guaranteed to be profitable
- Past performance ≠ future results

⚠️ **Technical Risk**
- Browser automation can break if Polymarket UI changes
- Network issues can cause missed trades
- Always monitor the system

## Performance Tracking

Coming soon:
- P&L dashboard
- Win rate statistics
- Trade journal
- Position tracking

## Roadmap

- [x] Signal generation
- [x] Autonomous execution
- [ ] Position sizing based on Kelly criterion
- [ ] P&L tracking
- [ ] WhatsApp notifications on trades
- [ ] Multi-account support
- [ ] Trailing stop losses
- [ ] Compounding profits

---

**Built for Polymarket 15M markets. Use responsibly.**
