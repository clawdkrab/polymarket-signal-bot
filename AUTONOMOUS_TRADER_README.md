# Autonomous 15M Trader with MetaMask Auto-Confirm

## Features

✅ **Stays on /crypto/15M** - Never leaves the page  
✅ **60-second refresh** - Checks for new markets every minute  
✅ **15-minute full reload** - Catches new market cycles  
✅ **MetaMask auto-confirm** - Automatically clicks "Confirm" in MetaMask popups  
✅ **$10 position size** - Conservative starting amount  
✅ **BTC momentum strategy** - Uses Binance 15m data  

## Quick Start

```bash
cd ~/clawd/polymarket-btc-agent

# Run with visible browser (recommended first time)
python3 autonomous_15m_trader.py

# Or headless (background)
python3 autonomous_15m_trader.py --headless

# Custom position size
python3 autonomous_15m_trader.py --position-size 15
```

## How It Works

### 1. **Browser Session**
- Uses persistent browser context (saves your MetaMask connection)
- Keeps you logged into Polymarket
- No need to reconnect wallet each time

### 2. **Trading Cycle** (every 60 seconds)
1. Refresh /crypto/15M page
2. Fetch BTC 15m momentum from Binance
3. If momentum > 0.3% → Signal UP
4. If momentum < -0.3% → Signal DOWN
5. If confidence ≥ 60% → Execute trade

### 3. **Trade Execution**
1. Click "Up" or "Down" button
2. Enter $10 amount
3. Click "Buy" button
4. **DETECT MetaMask popup**
5. **AUTO-CLICK "Confirm" button**
6. Wait for confirmation
7. Log trade to `trades_log.jsonl`
8. Cool down 2 minutes

### 4. **Full Reload** (every 15 minutes)
- Completely reloads page
- Catches new market cycles when old ones expire

## MetaMask Auto-Confirm

The script automatically:
1. Detects when MetaMask popup opens (new window)
2. Finds the "Confirm" button
3. Clicks it
4. Closes the popup

**No manual clicking required!**

## Logs

All trades saved to `trades_log.jsonl`:

```json
{"timestamp": "2026-01-28T16:00:00", "direction": "DOWN", "amount": 10.0, "status": "SUCCESS", "trades_count": 1}
{"timestamp": "2026-01-28T16:15:30", "direction": "UP", "amount": 10.0, "status": "SUCCESS", "trades_count": 2}
```

## Safety Features

- **Confidence threshold**: Only trades when momentum signal ≥ 60%
- **Cooling period**: Waits 2 minutes after each trade
- **Error handling**: Logs failures and continues
- **Position limit**: Fixed $10 (configurable)

## Monitoring

Watch the console output:
```
CYCLE #5 | 16:15:30
Trades today: 2
==================
♻️  Refreshing page...
   📊 BTC: $89,500 | Momentum: +0.45%
💡 Signal: UP | Confidence: 65%
🚨 EXECUTING TRADE
Direction: UP | Amount: $10.00
🖱️  Clicking Up button...
⌨️  Entering amount $10.00...
🖱️  Clicking Buy button...
🔐 Waiting for MetaMask...
   ✅ MetaMask popup detected
   ✅ Auto-confirmed in MetaMask!
✅ TRADE EXECUTED SUCCESSFULLY
✅ Trade #3 completed!
⏸️  Waiting 60 seconds until next check...
```

## Troubleshooting

**"MetaMask auto-confirm failed"**
→ MetaMask might have changed UI. Script will wait 10s for manual click.

**"No MetaMask popup detected"**
→ Trade might not need confirmation (already approved). Check Polymarket.

**Trade shows "UNCERTAIN"**
→ Check Polymarket portfolio manually to verify.

**Script crashes**
→ Check that Playwright is installed: `playwright install chromium`

## Stop the Bot

Press `Ctrl+C` to stop gracefully. Final stats will be displayed.

## Deploy to Replit (24/7)

1. Create new Repl (Python)
2. Import from GitHub: `clawdkrab/polymarket-btc-agent`
3. Install deps: `pip install playwright requests`
4. Run: `playwright install chromium`
5. Run: `python autonomous_15m_trader.py --headless`
6. Keep Repl always on

## Next Steps

- Increase position size after proving profitability
- Add WhatsApp notifications (use `notify_whatsapp.py`)
- Track P&L and win rate
- Adjust momentum thresholds based on performance
