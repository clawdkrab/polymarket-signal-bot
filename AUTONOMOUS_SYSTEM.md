# AUTONOMOUS SYSTEM - 24/7 BTC Trading Bot

## Architecture

The system is now split into two independent, always-running processes:

### 1. Continuous Signal Engine (`continuous_signal_engine.py`)
- **Runs forever** - never stops, never waits for chat
- Generates BTC directional predictions every 3 seconds
- Always maintains a directional thesis (UP / DOWN / NO_TRADE) for the next 15-minute window
- Writes signal to `signal.json` in real-time
- Logs periodic snapshots to `signals.jsonl`

**Signal Calculation:**
- Momentum (30s, 60s, 120s equivalent via 15m interpolation)
- Momentum acceleration/deceleration
- Volatility regime (expanding/contracting)
- Trend bias (micro vs macro)
- Mean reversion pressure
- Multi-factor scoring with weighted components

**Output:** `signal.json` contains:
```json
{
  "timestamp": "2026-01-28T17:30:42Z",
  "direction": "UP",
  "confidence": 74,
  "price": 89617.0,
  "basis": {
    "momentum_30s": 0.21,
    "momentum_120s": 0.44,
    "volatility_state": "expanding",
    "trend_bias": "strong_up",
    "mean_reversion_pressure": "low",
    "score": 0.65
  }
}
```

### 2. Autonomous Trade Executor (`autonomous_trade_executor.py`)
- **Runs forever** - independent of signal engine
- Uses Playwright with persistent Chrome profile (clawdkrab@gmail.com)
- Stays on `https://polymarket.com/crypto/15M`
- Polls DOM every 5-10 seconds
- Detects new 15-minute markets by timestamp
- Reads `signal.json` when new market appears
- Executes trade if confidence >= threshold
- Auto-confirms MetaMask transactions
- Enforces cooldown period between trades

**Execution Flow:**
1. Detect new market at :00, :15, :30, :45
2. Read precomputed signal from disk
3. If confidence >= 60%: execute trade
4. Auto-click MetaMask confirm
5. Log result to `trades.jsonl`
6. Cooldown for 2 minutes

### 3. Supervisor (`supervisor.sh`)
- Process manager for both components
- Auto-restart on crash
- Background execution
- Independent of chat/terminal

---

## Startup

### One-Command Start
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
./supervisor.sh start
```

This will:
- Launch signal engine in background
- Launch trade executor in background
- Display system status
- Exit (processes continue running)

### Configuration
Set environment variables before starting:
```bash
export POSITION_SIZE=10.0          # Trade size in USD
export CONFIDENCE=60               # Minimum confidence threshold
export CHROME_PROFILE=Default      # Chrome profile name
export METAMASK_PASSWORD=yourpass  # Optional: auto-unlock MetaMask

./supervisor.sh start
```

---

## Control Commands

### Check Status
```bash
./supervisor.sh status
```
Shows:
- Process status (running/stopped)
- Process IDs
- Current signal
- Trade count

### Stop System
```bash
./supervisor.sh stop
```
Stops both processes cleanly.

### Restart System
```bash
./supervisor.sh restart
```
Stop + Start in one command.

### View Logs
```bash
./supervisor.sh logs
```
Tail both log files in real-time.

---

## Log Files

| File | Purpose |
|------|---------|
| `signal.json` | Current signal (updated every 3s) |
| `signals.jsonl` | Historical signal snapshots (1/min) |
| `trades.jsonl` | Trade execution log |
| `errors.log` | Error log |
| `signal_engine.log` | Signal engine output |
| `trade_executor.log` | Trade executor output |

---

## Chrome Profile Setup

The trade executor uses your existing Chrome profile with MetaMask installed.

**Default:** `Default` profile at:
```
~/Library/Application Support/Google/Chrome/Default
```

**Custom profile:** Use `--profile` argument:
```bash
python3 autonomous_trade_executor.py --profile "Profile 1"
```

**MetaMask Setup:**
1. Ensure MetaMask extension is installed
2. Wallet must be connected to Polymarket
3. Optional: Set `METAMASK_PASSWORD` env var for auto-unlock

---

## Signal Engine Details

### Continuous Operation
The signal engine **never stops**:
- Runs in infinite loop
- Fetches BTC price data every 3 seconds
- Recalculates signal immediately
- Writes to disk atomically
- Auto-restarts on crash

### Signal Logic
Multi-factor scoring system:

| Component | Weight | Bullish Signal | Bearish Signal |
|-----------|--------|----------------|----------------|
| Momentum (30s) | 40% | > +0.2% | < -0.2% |
| Momentum Accel | 20% | > +0.15% | < -0.15% |
| Trend | 20% | Strong up | Strong down |
| Volatility | 10% | Expanding | - |
| Mean Reversion | 10% | Oversold | Overbought |

**Score range:** -1.0 to +1.0
**Threshold:** ±0.25 required to generate signal

**Confidence calculation:**
```python
if score > 0.25:
    confidence = min(95, 50 + (score * 100))
```

---

## Trade Executor Details

### Market Detection
Detects new markets by checking timestamp:
- Markets appear at :00, :15, :30, :45
- Only trades once per 15-minute window
- Enforces 2-minute cooldown after trade

### Trade Execution Steps
1. Click "Up" or "Down" button
2. Enter position size
3. Click "Buy Up" / "Buy Down"
4. Wait for MetaMask popup
5. Auto-click "Confirm"
6. Verify trade success
7. Log result

### MetaMask Auto-Confirm
When MetaMask popup appears:
1. Detect new browser tab/popup
2. Check for unlock screen (if locked)
3. Enter password if `METAMASK_PASSWORD` set
4. Click "Confirm" button
5. Close popup
6. Return to Polymarket tab

**Fallback:** If auto-confirm fails, wait 15 seconds for manual confirmation.

---

## Process Lifecycle

### Background Execution
Both processes run via `nohup` in background:
- Detached from terminal
- Continue after logout
- Survive shell exit
- Independent of chat session

### Auto-Restart
Signal engine has built-in auto-restart:
- Catches exceptions
- Logs error
- Waits 10 seconds
- Restarts loop

Trade executor restarts browser on crash:
- Detects browser failure
- Closes cleanly
- Waits 10 seconds
- Launches new instance
- Resumes monitoring

### Manual Restart
```bash
./supervisor.sh restart
```
Or kill and restart individual processes:
```bash
pkill -f continuous_signal_engine.py
python3 continuous_signal_engine.py &
```

---

## Dependencies

Required Python packages:
```bash
pip install playwright requests numpy
playwright install chromium
```

System requirements:
- macOS (or Linux with Chrome installed)
- Google Chrome browser
- MetaMask extension
- Python 3.8+

---

## Monitoring

### Real-Time Signal
```bash
watch -n 1 'cat signal.json | python3 -m json.tool'
```

### Recent Trades
```bash
tail -20 trades.jsonl | jq
```

### Process Check
```bash
ps aux | grep -E "continuous_signal|autonomous_trade"
```

### Resource Usage
```bash
top -pid $(pgrep -f continuous_signal_engine.py)
top -pid $(pgrep -f autonomous_trade_executor.py)
```

---

## Troubleshooting

### Signal Engine Not Starting
```bash
python3 continuous_signal_engine.py
# Check for import errors or missing dependencies
```

### Trade Executor Can't Find Chrome Profile
```bash
ls -la ~/Library/Application\ Support/Google/Chrome/
# Verify profile directory exists
```

### MetaMask Not Confirming
1. Check `METAMASK_PASSWORD` is set correctly
2. Verify MetaMask is unlocked
3. Check trade_executor.log for popup detection issues
4. Increase wait times in `handle_metamask()` method

### Browser Crashes
- Check available memory
- Ensure Chrome isn't already running with same profile
- Try different Chrome profile
- Check trade_executor.log for specific errors

---

## Success Criteria

System is working correctly when:

✅ Signal engine prints updates every 3 seconds  
✅ `signal.json` file updates continuously  
✅ Trade executor stays on /crypto/15M page  
✅ New markets trigger signal reads  
✅ Trades execute when confidence >= threshold  
✅ MetaMask confirms automatically  
✅ Trades log to `trades.jsonl`  
✅ System continues running after chat silence  
✅ Processes auto-restart on crash  

---

## Key Differences from Old System

| Old System | New System |
|------------|------------|
| Reactive (triggered by chat) | Proactive (always hunting) |
| Signal computed at trade time | Signal precomputed continuously |
| Browser Relay (Clawdbot tool) | Playwright (direct control) |
| Manual MetaMask | Auto MetaMask |
| Chat-dependent | Chat-independent |
| Stops when idle | Never stops |
| Unknown direction until asked | Always has directional conviction |

---

## Architecture Diagram

```
┌─────────────────────────────────┐
│   Continuous Signal Engine      │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Fetch BTC price (3s)    │   │
│  └──────────┬──────────────┘   │
│             │                   │
│  ┌──────────▼──────────────┐   │
│  │ Multi-factor analysis   │   │
│  │ - Momentum              │   │
│  │ - Volatility            │   │
│  │ - Trend                 │   │
│  │ - Mean reversion        │   │
│  └──────────┬──────────────┘   │
│             │                   │
│  ┌──────────▼──────────────┐   │
│  │ Write signal.json       │   │
│  └─────────────────────────┘   │
│                                 │
│  Loop forever (never stop)      │
└─────────────────────────────────┘
                │
                │ signal.json
                ▼
┌─────────────────────────────────┐
│   Autonomous Trade Executor     │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Monitor /crypto/15M     │   │
│  └──────────┬──────────────┘   │
│             │                   │
│  ┌──────────▼──────────────┐   │
│  │ Detect new market?      │   │
│  │ (every 10s)             │   │
│  └──────────┬──────────────┘   │
│             │ YES               │
│  ┌──────────▼──────────────┐   │
│  │ Read signal.json        │   │
│  └──────────┬──────────────┘   │
│             │                   │
│  ┌──────────▼──────────────┐   │
│  │ Confidence >= 60%?      │   │
│  └──────────┬──────────────┘   │
│             │ YES               │
│  ┌──────────▼──────────────┐   │
│  │ Execute trade           │   │
│  │ - Click Up/Down         │   │
│  │ - Enter amount          │   │
│  │ - Auto-confirm MetaMask │   │
│  └──────────┬──────────────┘   │
│             │                   │
│  ┌──────────▼──────────────┐   │
│  │ Log to trades.jsonl     │   │
│  └─────────────────────────┘   │
│                                 │
│  Loop forever (never stop)      │
└─────────────────────────────────┘
```

---

## Final Notes

- **Signal generation and trade execution are completely decoupled**
- **Both processes run independently and never block each other**
- **System is fully autonomous after `./supervisor.sh start`**
- **Chat can inspect but never controls runtime**
- **Processes survive disconnections, reboots (with cron), and crashes**

This is a **true 24/7 autonomous trading system**.
