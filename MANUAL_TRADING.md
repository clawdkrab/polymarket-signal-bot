# MANUAL TRADING GUIDE

## Overview

The signal engine continuously analyzes BTC and generates trading signals every 3 seconds. This guide shows how to use these signals for **manual trading** on Polymarket.

---

## Quick Start

### 1. Start Signal Engine Only
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
nohup python3 -u continuous_signal_engine.py > signal_engine.log 2>&1 &
```

### 2. Check Current Signal
```bash
./signal-now.sh
```

Example output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BTC 15M SIGNAL - 18:35:42 UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Direction:  DOWN
   Confidence: 85%
   BTC Price:  $89,735.99

📈 Technical Basis:
   Momentum 30s:  -0.450%
   Momentum 60s:  -0.320%
   Momentum 120s: -0.185%
   Volatility:    0.285% (expanding)
   Trend Bias:    strong_down
   Score:         -0.65

💡 Recommendation:
   👉 STRONG BUY DOWN - High confidence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. Watch Signals in Real-Time
```bash
./watch-signals.sh
```

This shows live updating signal (refreshes every 3 seconds).

---

## Signal Interpretation

### Direction
- **🟢 UP** - BTC expected to go up in next 15 minutes
- **🔴 DOWN** - BTC expected to go down in next 15 minutes
- **⚪ NO_TRADE** - No clear direction, confidence too low

### Confidence Levels
- **70%+** - Strong signal, high conviction trade
- **60-69%** - Moderate signal, reasonable trade
- **50-59%** - Weak signal, risky
- **<50%** - No trade, wait for better setup

### Technical Components

**Momentum (30s, 60s, 120s)**
- Positive (+) = Upward price movement
- Negative (-) = Downward price movement
- Shows recent price velocity at different timeframes

**Volatility**
- `expanding` = Price swings increasing (more opportunity)
- `contracting` = Price swings decreasing (less movement)
- Higher % = More volatile

**Trend Bias**
- `strong_up` / `strong_down` = Clear directional trend
- `weak_up` / `weak_down` = Mild trend
- `neutral` = No clear trend

**Score**
- Range: -1.0 to +1.0
- Positive = Bullish
- Negative = Bearish
- Magnitude = Strength of conviction

---

## Trading Workflow

### Before Markets Open

1. **Check signal 2-3 minutes before market opens** (:00, :15, :30, :45)
   ```bash
   ./signal-now.sh
   ```

2. **Review confidence level**
   - 70%+ = Strong trade
   - 60-69% = Consider trade
   - <60% = Skip this window

3. **Open Polymarket**
   ```
   https://polymarket.com/crypto/15M
   ```

4. **Wait for new market to appear**
   - Markets open at :00, :15, :30, :45
   - Look for "Bitcoin Up or Down" card
   - Check it's the NEW 15-minute window

### Executing Trade

5. **Place order according to signal**
   - Signal = UP → Click "Up" button → Enter amount → Buy Up
   - Signal = DOWN → Click "Down" button → Enter amount → Buy Down

6. **Confirm in MetaMask**
   - Review transaction
   - Click "Confirm"
   - Wait for confirmation

7. **Verify position**
   - Check Polymarket shows your position
   - Note entry price and amount

### After Trade

8. **Log your trade** (optional but recommended)
   ```bash
   echo "$(date -u +%Y-%m-%dT%H:%M:%S) | Direction: DOWN | Amount: $10 | Confidence: 85%" >> my_trades.txt
   ```

9. **Monitor outcome**
   - Watch market until it resolves (15 minutes)
   - Track win/loss
   - Review what the signal got right/wrong

---

## Position Sizing (Recommended)

Start conservative and scale up as you gain confidence:

| Experience Level | Position Size | Risk Level |
|------------------|---------------|------------|
| Testing signals  | $5-10 | Very Low |
| Learning (1-2 weeks) | $10-25 | Low |
| Confident (1+ month) | $25-50 | Moderate |
| Experienced (3+ months) | $50-100 | Higher |

**Never risk more than you can afford to lose on a single trade.**

---

## When to Trade

### High-Probability Setups
✅ Confidence >= 70%  
✅ Clear trend bias (strong_up/strong_down)  
✅ All momentum indicators aligned (30s, 60s, 120s same direction)  
✅ Expanding volatility  

### Medium-Probability Setups
⚠️  Confidence 60-69%  
⚠️  Mixed momentum signals  
⚠️  Contracting volatility  

### Skip These
❌ Confidence < 60%  
❌ Direction = NO_TRADE  
❌ Conflicting momentum signals  
❌ You're uncertain or uncomfortable  

---

## Market Timing

### 15-Minute Windows
Markets open at:
- :00 - :15
- :15 - :30
- :30 - :45
- :45 - :00

### When to Check Signal
- **2-3 minutes before** market opens (e.g., at :12-13 for :15 market)
- Signal is continuously updated, so it's fresh
- Don't check too early (signal may change)

### Best Times to Trade
Based on volatility and volume:
- **16:00-20:00 UTC** (afternoon US, evening Europe) - High activity
- **13:00-16:00 UTC** (morning US, afternoon Europe) - Moderate activity
- **00:00-06:00 UTC** (night US, morning Asia) - Lower activity

---

## Signal Quality Check

Before trading, verify signal quality:

```bash
./signal-now.sh
```

**Green flags (good signal):**
- ✅ Confidence >= 70%
- ✅ Clear direction (UP or DOWN, not NO_TRADE)
- ✅ Momentum aligned across timeframes
- ✅ Score magnitude > 0.5
- ✅ Trend bias matches direction

**Red flags (skip trade):**
- ❌ Confidence < 60%
- ❌ Direction = NO_TRADE
- ❌ Momentum conflicting (30s up, 120s down)
- ❌ Score near zero (-0.2 to +0.2)
- ❌ Signal changed direction in last minute

---

## Monitoring Tools

### Real-Time Monitor
```bash
./watch-signals.sh
```
Shows live updating signal. Press Ctrl+C to exit.

### Single Snapshot
```bash
./signal-now.sh
```
Shows detailed signal breakdown once.

### Raw Signal File
```bash
cat signal.json | python3 -m json.tool
```
View raw JSON data.

### Signal History
```bash
tail -20 signals.jsonl
```
View last 20 signal snapshots (1 per minute).

### Check Signal Engine
```bash
ps aux | grep continuous_signal_engine | grep -v grep
```
Verify engine is running.

---

## Troubleshooting

### Signal not updating
```bash
# Check if engine is running
ps aux | grep continuous_signal_engine | grep -v grep

# If not running, start it
nohup python3 -u continuous_signal_engine.py > signal_engine.log 2>&1 &
```

### Old signal (stale timestamp)
```bash
# Check last update time
stat -f "%Sm" signal.json

# If old, restart engine
pkill -f continuous_signal_engine
nohup python3 -u continuous_signal_engine.py > signal_engine.log 2>&1 &
```

### Can't read signal
```bash
# Check file exists
ls -la signal.json

# Check permissions
chmod 644 signal.json
```

---

## Performance Tracking

Create a simple trading journal:

```bash
# Create journal file
echo "Date,Time,Direction,Confidence,Amount,Outcome,Notes" > trading_journal.csv

# After each trade, add entry:
echo "2026-01-28,18:30,DOWN,85,10,WIN,Strong momentum signal" >> trading_journal.csv
```

Track:
- Win rate by confidence level
- Best performing timeframes
- Signal types that work best for you
- Common mistakes

---

## Advanced: Signal Alerts (Optional)

### Desktop Notification (macOS)
```bash
#!/bin/bash
# save as: notify-strong-signal.sh

while true; do
    conf=$(cat signal.json | python3 -c "import json,sys; print(json.load(sys.stdin)['confidence'])")
    dir=$(cat signal.json | python3 -c "import json,sys; print(json.load(sys.stdin)['direction'])")
    
    if [ "$conf" -ge 75 ] && [ "$dir" != "NO_TRADE" ]; then
        osascript -e "display notification \"$dir at $conf%\" with title \"Strong Signal\""
    fi
    
    sleep 30
done
```

### WhatsApp Notification
If you have WhatsApp configured in Clawdbot, signals can be sent via `notify_whatsapp.py` (if it exists).

---

## Tips for Success

1. **Start with observation** - Watch signals for a few days before trading
2. **Track your results** - Keep a trading journal
3. **Be selective** - Only trade high-confidence signals (70%+)
4. **Don't force trades** - It's okay to skip windows
5. **Review and learn** - After each trade, review what happened
6. **Manage risk** - Never risk more than you can afford to lose
7. **Stay disciplined** - Follow your rules, don't chase losses
8. **Take breaks** - Trading every window leads to burnout

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./signal-now.sh` | Show current signal |
| `./watch-signals.sh` | Live signal monitor |
| `tail -f signal_engine.log` | View engine logs |
| `cat signal.json` | Raw signal data |
| `tail -20 signals.jsonl` | Signal history |

---

## Next Steps

Once you're comfortable with manual trading:
1. Track your win rate over 20+ trades
2. Identify which signal types work best
3. Refine confidence thresholds
4. Consider re-enabling autonomous execution

For autonomous trading, see `START.md` and `AUTONOMOUS_SYSTEM.md`.

---

**Happy trading! Remember: Signals are guidance, not guarantees. Always do your own analysis.**
