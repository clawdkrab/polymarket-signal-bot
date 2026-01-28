# VERIFICATION CHECKLIST

## Pre-Launch Verification

Run these checks BEFORE starting the system:

### 1. Dependencies
```bash
python3 -c "import playwright, requests, numpy; print('✅ All dependencies OK')"
```
Expected: ✅ All dependencies OK

### 2. Chrome Profile
```bash
ls -la ~/Library/Application\ Support/Google/Chrome/Default/Preferences
```
Expected: File exists

### 3. Signal Engine Test
```bash
cd /Users/clawd/clawd/polymarket-btc-agent
python3 -c "
from continuous_signal_engine import ContinuousSignalEngine
engine = ContinuousSignalEngine()
signal = engine.generate_signal()
print(f'✅ Signal: {signal[\"direction\"]} at {signal[\"confidence\"]}% confidence')
"
```
Expected: ✅ Signal: [UP/DOWN/NO_TRADE] at [0-100]% confidence

### 4. Playwright Browser Test
```bash
python3 -c "
from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
browser = pw.chromium.launch()
print('✅ Playwright OK')
browser.close()
pw.stop()
"
```
Expected: ✅ Playwright OK

### 5. File Permissions
```bash
ls -la supervisor.sh
```
Expected: `-rwxr-xr-x` (executable)

---

## Post-Launch Verification

After running `./supervisor.sh start`, verify:

### 1. Processes Running
```bash
./supervisor.sh status
```
Expected:
```
Signal Engine:  ✅ RUNNING (PID: xxxxx)
Trade Executor: ✅ RUNNING (PID: xxxxx)
```

### 2. Signal File Created
```bash
ls -la signal.json
cat signal.json
```
Expected: File exists and contains valid JSON

### 3. Logs Generating
```bash
tail -5 signal_engine.log
tail -5 trade_executor.log
```
Expected: Recent timestamps in logs

### 4. Signal Engine Active
```bash
tail -20 signal_engine.log | grep "🎯"
```
Expected: Recent signal updates

### 5. Trade Executor on Page
```bash
tail -20 trade_executor.log | grep "crypto/15M"
```
Expected: "✅ At crypto/15M page"

### 6. No Critical Errors
```bash
grep -i "fatal\|critical" signal_engine.log trade_executor.log
```
Expected: Empty or no recent errors

### 7. Signal Updates Continuously
```bash
# Wait 10 seconds between checks
cat signal.json | python3 -c "import sys, json; print(json.load(sys.stdin)['timestamp'])"
sleep 10
cat signal.json | python3 -c "import sys, json; print(json.load(sys.stdin)['timestamp'])"
```
Expected: Two different timestamps

---

## Runtime Verification (After 15 Minutes)

### 1. System Still Running
```bash
./supervisor.sh status
```
Expected: Both processes ✅ RUNNING

### 2. Multiple Signals Logged
```bash
wc -l signals.jsonl
```
Expected: Multiple lines (1 per minute)

### 3. Chrome Still Open
```bash
ps aux | grep -i chrome | grep -v grep | wc -l
```
Expected: > 0 (Chrome process running)

### 4. No Memory Leaks
```bash
ps aux | grep "continuous_signal_engine.py" | awk '{print $4"%"}'
ps aux | grep "autonomous_trade_executor.py" | awk '{print $4"%"}'
```
Expected: Memory usage < 5% each

---

## Trade Verification (After First Trade)

### 1. Trade Logged
```bash
tail -1 trades.jsonl
```
Expected: JSON with direction, amount, status

### 2. Trade Successful
```bash
tail -1 trades.jsonl | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])"
```
Expected: "SUCCESS"

### 3. Position on Polymarket
Manual: Check Polymarket UI for active position

### 4. MetaMask Transaction
Manual: Check MetaMask activity for confirmed transaction

---

## Failure Scenarios

Test these to ensure auto-recovery:

### 1. Kill Signal Engine
```bash
pkill -f continuous_signal_engine.py
sleep 5
./supervisor.sh status
```
Expected: Process automatically restarted

### 2. Kill Trade Executor
```bash
pkill -f autonomous_trade_executor.py
sleep 5
./supervisor.sh status
```
Expected: Process automatically restarted

### 3. Delete Signal File
```bash
rm signal.json
sleep 5
ls -la signal.json
```
Expected: File recreated within seconds

### 4. Network Interruption
```bash
# Disconnect WiFi for 30 seconds, then reconnect
# Monitor logs during reconnection
tail -f signal_engine.log
```
Expected: Temporary errors, then recovery

---

## Success Criteria

System is fully operational when ALL checks pass:

✅ Both processes running continuously  
✅ Signal file updates every 3 seconds  
✅ Signals.jsonl grows every minute  
✅ Chrome browser stays on crypto/15M page  
✅ No fatal errors in logs  
✅ Memory usage stable (< 5% each)  
✅ System survives process kills (auto-restart)  
✅ System survives network interruptions  
✅ Trades execute when markets appear  
✅ MetaMask confirms automatically  
✅ Trades log correctly  

---

## Red Flags

Stop and investigate if you see:

🚨 Process not restarting after kill  
🚨 Signal file not updating  
🚨 Memory usage growing continuously  
🚨 Chrome crashing repeatedly  
🚨 MetaMask not confirming (no popup or frozen)  
🚨 Trades failing consistently  
🚨 Error log growing rapidly  

---

## Debug Commands

### Full System Status
```bash
echo "=== PROCESSES ==="
ps aux | grep -E "continuous_signal|autonomous_trade" | grep -v grep
echo ""
echo "=== FILES ==="
ls -lah signal.json signals.jsonl trades.jsonl 2>/dev/null
echo ""
echo "=== CURRENT SIGNAL ==="
cat signal.json 2>/dev/null | python3 -m json.tool
echo ""
echo "=== RECENT LOGS ==="
echo "Signal Engine:"
tail -3 signal_engine.log
echo ""
echo "Trade Executor:"
tail -3 trade_executor.log
```

### Monitor Everything
```bash
watch -n 2 './supervisor.sh status'
```

### Trace Signal Updates
```bash
while true; do
  timestamp=$(cat signal.json | python3 -c "import sys, json; print(json.load(sys.stdin)['timestamp'])")
  direction=$(cat signal.json | python3 -c "import sys, json; print(json.load(sys.stdin)['direction'])")
  confidence=$(cat signal.json | python3 -c "import sys, json; print(json.load(sys.stdin)['confidence'])")
  echo "[$(date +%H:%M:%S)] Signal: $direction ($confidence%) | TS: $timestamp"
  sleep 3
done
```

---

## Contact Points

If all verification passes:
✅ **System is fully autonomous and ready**

If verification fails:
1. Check logs: `./supervisor.sh logs`
2. Check errors: `cat errors.log`
3. Restart: `./supervisor.sh restart`
4. Re-run verification checklist

---

**Last Updated:** 2026-01-28  
**System Version:** Autonomous 24/7 v1.0
