# QUICK REFERENCE - Polymarket BTC Agent

## Current Configuration
- **Profile:** Profile 1 (polymarketv2@gmail.com)
- **Position Size:** $10.00
- **Confidence Threshold:** 60%
- **Markets:** 15-minute BTC Up/Down

---

## Status Check
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
./supervisor.sh status
```

---

## Control Commands
```bash
./supervisor.sh start     # Start both processes
./supervisor.sh stop      # Stop everything
./supervisor.sh restart   # Restart both
./supervisor.sh logs      # Tail both log files
```

---

## Monitor Signal (Real-Time)
```bash
# Option 1: Simple watch
watch -n 1 'cat signal.json | python3 -m json.tool'

# Option 2: One-line status
watch -n 3 'python3 -c "import json; s=json.load(open(\"signal.json\")); print(f\"{s[\"timestamp\"][11:19]} | {s[\"direction\"]:8s} | {s[\"confidence\"]:2d}% | ${s[\"price\"]:,.0f}\")"'

# Option 3: View signal history
tail -f signals.jsonl
```

---

## Monitor Trades
```bash
# Watch for new trades
tail -f trades.jsonl

# Count trades today
wc -l trades.jsonl

# View last trade
tail -1 trades.jsonl | python3 -m json.tool
```

---

## View Logs
```bash
# Signal engine log
tail -f signal_engine.log

# Trade executor log
tail -f trade_executor.log

# Both logs together
tail -f signal_engine.log trade_executor.log

# Or use supervisor
./supervisor.sh logs
```

---

## Troubleshooting

### System not starting
```bash
# Check if Chrome is running
ps aux | grep "Google Chrome" | grep -v grep

# If yes, close it
pkill -x "Google Chrome"

# Then restart
./supervisor.sh restart
```

### Signal not updating
```bash
# Check signal engine process
ps aux | grep continuous_signal_engine | grep -v grep

# If not running, restart
./supervisor.sh restart

# Check logs
tail -50 signal_engine.log
```

### Trade executor not working
```bash
# Check if process is running
ps aux | grep autonomous_trade_executor | grep -v grep

# Check if Chrome launched
ps aux | grep "Google Chrome" | grep -v grep

# Check logs
tail -100 trade_executor.log
```

### Check if bot is on right page
Look for Chrome window with "Polymarket Bot" profile - should be on:
`https://polymarket.com/crypto/15M`

---

## Emergency Stop
```bash
# Stop everything immediately
./supervisor.sh stop

# Or kill manually
pkill -f continuous_signal_engine.py
pkill -f autonomous_trade_executor.py
pkill -x "Google Chrome"
```

---

## Change Settings

### Change position size
```bash
export POSITION_SIZE=15.0
./supervisor.sh restart
```

### Change confidence threshold
```bash
export CONFIDENCE=70
./supervisor.sh restart
```

### Use different profile
```bash
export CHROME_PROFILE="Default"
./supervisor.sh restart
```

### Set MetaMask password (auto-unlock)
```bash
export METAMASK_PASSWORD=yourpassword
./supervisor.sh restart
```

---

## Files to Monitor

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `signal.json` | Current signal | Every 3 seconds |
| `signals.jsonl` | Signal history | Every minute |
| `trades.jsonl` | Trade log | When trades execute |
| `errors.log` | Error log | When errors occur |
| `signal_engine.log` | Engine stdout/stderr | Continuous |
| `trade_executor.log` | Executor stdout/stderr | Continuous |

---

## Expected Behavior

### Normal Operation
- Signal updates every 3 seconds
- Chrome stays on /crypto/15M page
- At :00 :15 :30 :45, bot checks for new market
- If confidence >= 60%, executes trade
- MetaMask auto-confirms
- 2-minute cooldown after trade

### First Trade Timeline
1. Bot starts
2. Signal engine begins analyzing (immediately)
3. Trade executor navigates to page (~10-30 seconds)
4. Wait for next market window (max 15 minutes)
5. Execute trade if confidence >= threshold
6. Total time to first trade: 0-15 minutes

---

## Success Indicators

✅ Both processes show as RUNNING in status  
✅ signal.json updates every 3 seconds  
✅ Chrome window open on /crypto/15M  
✅ No errors in error.log  
✅ Memory usage stable  

---

## Red Flags

🚨 Process crashes and doesn't restart  
🚨 Signal.json stops updating  
🚨 Chrome not opening  
🚨 MetaMask popup not closing  
🚨 Trades failing repeatedly  
🚨 Error log growing rapidly  

---

## Daily Maintenance

1. Check status once: `./supervisor.sh status`
2. Review trades: `cat trades.jsonl`
3. Check for errors: `tail -20 errors.log`
4. Verify both processes still running

That's it!

---

## Performance Tips

- **Let it run:** Don't restart unless necessary
- **Monitor from logs:** Don't interact with Chrome window
- **Weekly review:** Check trade performance, adjust confidence if needed
- **Backup logs:** Archive old .jsonl files weekly

---

## Contact / Support

- Documentation: See AUTONOMOUS_SYSTEM.md
- Troubleshooting: See VERIFICATION.md
- Architecture: See TRANSFORMATION.md

---

**Last Updated:** 2026-01-28  
**System Version:** Autonomous 24/7 v1.0  
**Profile:** Profile 1 (polymarketv2@gmail.com)
