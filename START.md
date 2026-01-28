# START - Quick Launch Guide

## Prerequisites
✅ Python 3.8+ installed  
✅ Dependencies installed: `pip install playwright requests numpy`  
✅ Chrome browser with MetaMask extension  
✅ MetaMask connected to Polymarket  
✅ MetaMask has funds for trading  
⚠️  **IMPORTANT:** Close all Chrome windows before starting (profile must not be in use)  

## Pre-Launch Check

Before starting, ensure Chrome is completely closed:

```bash
# Check if Chrome is running
ps aux | grep -i chrome | grep -v grep

# If Chrome is running, close all windows or kill it:
pkill -x "Google Chrome"
```

**Why?** Playwright needs exclusive access to the Chrome profile.

## Launch (One Command)

**Easiest way:**
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
./start-bot.sh
```

**Or manually with supervisor:**
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
export CHROME_PROFILE="Profile 1"
./supervisor.sh start
```

**That's it.** System is now running 24/7 in background.

## Configuration (Optional)

Before starting, set environment variables:

```bash
# Trade settings
export POSITION_SIZE=10.0          # USD per trade (default: $10)
export CONFIDENCE=60               # Min confidence % (default: 60)
export CHROME_PROFILE=Default      # Chrome profile name

# MetaMask auto-unlock (optional)
export METAMASK_PASSWORD=yourpass  # Skip if you want manual unlock

# Then start
./supervisor.sh start
```

## Check Status

```bash
./supervisor.sh status
```

Output:
```
📊 System Status
==================================
Signal Engine:  ✅ RUNNING (PID: 12345)
Trade Executor: ✅ RUNNING (PID: 12346)
==================================

📡 Current Signal:
{
  "direction": "DOWN",
  "confidence": 95,
  "price": 89353.28,
  ...
}

📊 Trades executed: 3
```

## View Live Logs

```bash
./supervisor.sh logs
```

Press Ctrl+C to stop tailing.

## Stop System

```bash
./supervisor.sh stop
```

## Restart System

```bash
./supervisor.sh restart
```

## What Happens After Start

1. **Signal Engine** launches in background
   - Fetches BTC price every 3 seconds
   - Continuously computes directional signal
   - Writes to `signal.json`
   - Always has a trading thesis ready

2. **Trade Executor** launches in background
   - Opens Chrome with your MetaMask profile
   - Navigates to polymarket.com/crypto/15M
   - Polls page every 10 seconds
   - Waits for new 15-minute markets
   - Executes trades when signal is strong

3. **You can close this terminal**
   - Processes continue running
   - Chat disconnection doesn't affect them
   - They auto-restart on crash
   - Logs are written to disk

## First Trade

The system will:
1. Wait for next 15-minute market window (:00, :15, :30, :45)
2. Read precomputed signal
3. If confidence >= 60%, execute trade
4. Auto-confirm MetaMask
5. Log result

**Average time to first trade:** 0-14 minutes (depending on when you start)

## Monitor Signal in Real-Time

```bash
watch -n 1 'cat signal.json | python3 -m json.tool'
```

Or:
```bash
tail -f signals.jsonl
```

## Monitor Trades

```bash
tail -f trades.jsonl
```

## Troubleshooting

### No signal.json file
Wait 5 seconds after start. File is created on first signal generation.

### Trade executor not starting / No output in logs
Chrome is probably already running. Close it completely:
```bash
pkill -x "Google Chrome"
./supervisor.sh restart
```

### Trade executor can't find Chrome profile
Check profile name:
```bash
ls -la ~/Library/Application\ Support/Google/Chrome/
```
Then restart with correct profile:
```bash
export CHROME_PROFILE="Profile 1"
./supervisor.sh restart
```

### MetaMask not confirming automatically
Set password:
```bash
export METAMASK_PASSWORD=yourpassword
./supervisor.sh restart
```

Or confirm manually when popup appears.

### Processes crash immediately
Check logs:
```bash
tail -50 signal_engine.log
tail -50 trade_executor.log
```

## Safety

- System will NEVER trade more than position size
- Cooldown enforced: 2 minutes between trades
- Only trades when confidence >= threshold
- All trades logged to `trades.jsonl`
- All errors logged to `errors.log`

## Next Steps

After starting:
1. Wait for system to stabilize (30 seconds)
2. Check status: `./supervisor.sh status`
3. Monitor logs: `./supervisor.sh logs`
4. Wait for next 15-minute window
5. Watch first trade execute

## Architecture

- **Signal Engine:** Runs forever, generates signals continuously
- **Trade Executor:** Runs forever, executes on new markets
- **Supervisor:** Keeps both alive, restarts on crash
- **All independent of chat/terminal**

Read `AUTONOMOUS_SYSTEM.md` for full architecture details.

---

**You are now running a fully autonomous 24/7 BTC trading bot.**
