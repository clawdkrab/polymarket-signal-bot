# ✅ FULLY AUTOMATED POLYMARKET TRADING BOT

**Status:** LIVE and RUNNING (PID: 34527)

---

## 🤖 How It Works (100% Automated)

### Every 60 Seconds:

1. **Fetch BTC Price** (CoinCap/Binance API - Free)
2. **Calculate RSI & Momentum** (Technical analysis)
3. **Check Signal:**
   - RSI < 18 with 70%+ confidence = BUY signal
   - RSI > 72 with 70%+ confidence = SELL signal
   - Otherwise = No signal, wait

---

### When Signal Triggers (FULLY AUTOMATED):

#### **Step 1: Bot Detects Signal**
```
🚨 SIGNAL DETECTED
Action: UP
Size: $15.50
Confidence: 85%
RSI: 17.2
```

#### **Step 2: Automatic Browser Control**

Bot executes via subprocess calls to `clawdbot browser`:

```bash
# Navigate to Polymarket
clawdbot browser --profile clawdkrab-chrome --action navigate --target-url https://polymarket.com/markets/crypto

# Click UP or DOWN button
clawdbot browser --profile clawdkrab-chrome --action act --request '{"kind":"click","text":"UP"}'

# Enter amount
clawdbot browser --profile clawdkrab-chrome --action act --request '{"kind":"type","text":"15.50"}'

# Click Buy
clawdbot browser --profile clawdkrab-chrome --action act --request '{"kind":"click","text":"Buy"}'
```

#### **Step 3: MetaMask Approval**
- ✅ Browser automatically clicks through to MetaMask
- ⏳ **MetaMask popup appears**
- 👆 **USER CLICKS APPROVE** (only manual step - safety feature)
- ✅ Transaction executes on blockchain

#### **Step 4: Trade Complete**
- Logged to `live_trades.jsonl`
- Capital updated
- Bot continues monitoring

---

## 🔒 Safety Features

1. **MetaMask Approval Required** (manual safety check)
2. **Position Sizing:** 3-10% of capital based on confidence
3. **Max Trades:** 10 per day
4. **Stop Loss:** Automatic if drawdown > 20%
5. **Min Confidence:** 70% required to trade

---

## 📊 Current Status

**Bot:** Running (PID: 34527)
**Browser:** Chrome (clawdkrab@gmail.com) - Connected
**Balance:** $284.95
**Current RSI:** ~31 (neutral - no signal yet)
**Waiting For:** RSI < 18 or > 72

---

## 📂 Files

**Log:** `~/Desktop/projects/polymarket-btc-agent/trader.log`
**Trades:** `~/Desktop/projects/polymarket-btc-agent/src/memory/live_trades.jsonl`
**PID:** `~/Desktop/projects/polymarket-btc-agent/trader.pid`

---

## 🛠️ Commands

**Check Status:**
```bash
tail -f ~/Desktop/projects/polymarket-btc-agent/trader.log
```

**Stop Bot:**
```bash
kill $(cat ~/Desktop/projects/polymarket-btc-agent/trader.pid)
```

**Restart Bot:**
```bash
cd ~/Desktop/projects/polymarket-btc-agent
nohup python3 automated_trader.py > trader.log 2>&1 &
echo $! > trader.pid
```

---

## ✅ No Manual Intervention Needed

The bot will:
- ✅ Monitor BTC automatically
- ✅ Detect signals automatically
- ✅ Navigate browser automatically
- ✅ Click buttons automatically
- ✅ Enter amounts automatically
- ✅ Submit orders automatically

**Only you approve MetaMask** (safety feature)

---

Last Updated: 2026-01-27 05:43 GMT
