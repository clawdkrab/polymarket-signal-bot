# Polymarket Trading Bot - Clawdbot Integration

## Overview

The bot is ready for full automation. It analyzes BTC price action and generates trade signals. When a signal triggers, Clawdbot will execute the trade in YOUR Chrome browser.

---

## How It Works

### 1. Bot Monitors Bitcoin (Every 60s)
```python
# automated_trader.py runs continuously
signal = analyze_signal()  # RSI, momentum, confidence
```

### 2. Signal Triggers (RSI < 18 or > 72 with 70%+ confidence)
```json
{
  "action": "UP",
  "size": 15.50,
  "confidence": 85
}
```

### 3. Clawdbot Executes Trade in Chrome
**Browser:** clawdkrab-chrome (YOUR Chrome with MetaMask)  
**Tab:** Polymarket BTC Up/Down market  
**Actions:**
- Navigate to active 15-min market
- Click UP or DOWN button
- Enter amount ($15.50)
- Click Buy/Confirm
- Wait for MetaMask popup
- (You approve MetaMask transaction)

---

## Integration Steps

### Option A: Manual Clawdbot Control (Recommended First)

**Run the bot:**
```bash
cd ~/Desktop/projects/polymarket-btc-agent
python3 automated_trader.py
```

**When signal triggers:**
Bot will print trade details. You (Clawd the AI) use browser tool to:

```
browser.navigate(profile="clawdkrab-chrome", url="https://polymarket.com/markets/crypto")
browser.snapshot(profile="clawdkrab-chrome")  # Get page elements
browser.act(profile="clawdkrab-chrome", request={
  "kind": "click",
  "ref": "button-up"  # or "button-down"
})
browser.act(profile="clawdkrab-chrome", request={
  "kind": "type",
  "ref": "input-amount",
  "text": "15.50"
})
browser.act(profile="clawdkrab-chrome", request={
  "kind": "click",
  "ref": "button-buy"
})
```

### Option B: Cron Job (Fully Autonomous)

Create a cron job that runs `check_and_trade()` every 60s:

```bash
clawdbot cron add \
  --schedule "*/1 * * * *" \
  --job "Run Polymarket trading check" \
  --text "from automated_trader import check_and_trade; result = check_and_trade(); if result: print(f'TRADE: {result}')"
```

When signal triggers, cron job returns trade data → Clawdbot executes in browser.

---

## Current Status

✅ Bot analyzes BTC (working)  
✅ Generates signals (working)  
✅ Connected to clawdkrab-chrome browser (working)  
✅ Polymarket account funded ($284.95)  
✅ MetaMask connected  
⏳ Waiting for browser automation commands  

---

## Next Steps

1. **Test:** Run `python3 automated_trader.py` to verify monitoring works
2. **Integrate:** When signal triggers, use browser tool to execute
3. **Automate:** Set up cron or continuous loop with browser control

---

## Safety Notes

- MetaMask approval still requires manual click (safety feature)
- All trades logged to `src/memory/live_trades.jsonl`
- Position sizes: 3-10% of capital based on confidence
- Max trades per day: 10 (risk management)
- Stop if drawdown > 20%

---

Last Updated: 2026-01-27 05:38 GMT
