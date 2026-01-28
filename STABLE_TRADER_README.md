# Stable 15M Trader - Quick Start

## What It Does

✅ Stays on https://polymarket.com/crypto/15M  
✅ Refreshes every 60 seconds to check for new markets  
✅ Full page reload every 15 minutes (when markets expire)  
✅ Trades directly from the page (no clicking into markets)  
✅ Starts with $10 positions  
✅ Uses BTC momentum strategy (or falls back to simple Binance momentum)  

## Setup

```bash
cd ~/clawd/polymarket-btc-agent

# Make sure dependencies are installed
pip install playwright requests
playwright install chromium

# Verify price feed works
python3 -c "from src.data.price_feed import BTCPriceFeed; print('OK')"
```

## Run

```bash
# Default: $10 positions, visible browser
python3 stable_15m_trader.py

# Custom position size (e.g., $15)
python3 stable_15m_trader.py --position-size 15

# Headless mode (no visible browser)
python3 stable_15m_trader.py --headless
```

## First Time Setup

1. **Connect Wallet**: When the browser opens, you'll be prompted to connect your MetaMask wallet if it's not already connected.

2. **Let it run**: The script will:
   - Navigate to https://polymarket.com/crypto/15M
   - Scan for active BTC Up/Down markets every 60 seconds
   - Analyze BTC momentum
   - Execute trades when signal confidence > 60%
   - Reload the page every 15 minutes

3. **Stop**: Press `Ctrl+C` to stop gracefully

## What to Monitor

- **Console output**: Shows each cycle (scan → analyze → trade/pass)
- **Trade log**: `trades_log.jsonl` contains all executed trades
- **Browser**: Keep visible to verify trades are executing

## Troubleshooting

**"Wallet not connected"**  
→ Connect MetaMask in the browser window, then press ENTER

**"No active markets found"**  
→ Markets may be between cycles. Wait 60 seconds for next check.

**"Trade execution failed"**  
→ Check if:
  - Wallet has sufficient USDC balance
  - Polymarket UI changed (button selectors may need updating)
  - Network connection is stable

**Trade executes but shows "UNCERTAIN"**  
→ Trade may have succeeded but confirmation wasn't detected. Check Polymarket UI manually.

## Safety Features

- ✅ Only trades when momentum signal confidence > 60%
- ✅ Waits 2 minutes after each trade (cooling period)
- ✅ Logs all trades to `trades_log.jsonl`
- ✅ Tracks capital to prevent over-trading
- ✅ Uses persistent browser session (wallet stays connected)

## Advanced

### Change Strategy Thresholds

Edit these lines in `stable_15m_trader.py`:

```python
# Line 164: Minimum confidence to trade
if confidence < 60:  # Change to 70 for more conservative

# Line 289: Momentum threshold for fallback strategy
if momentum > 0.5:  # Change to 1.0 for stronger signals only
```

### Increase Frequency

```python
# Line 559: Wait time between checks
time.sleep(60)  # Change to 30 for 30-second checks
```

## Expected Behavior

**Normal cycle:**
```
🔍 Scanning for active markets...
✅ Found 2 active markets
📈 Analyzing BTC price action...
   Signal: UP | Confidence: 65%
💡 Signal: UP | Confidence: 65% | Reason: Momentum +0.82%
🚨 EXECUTING TRADE
   Direction: UP | Amount: $10.00
🖱️  Clicking UP button...
⌨️  Entering amount...
✅ Entered $10.00
🖱️  Looking for confirm button...
✅ Found button: Buy
🖱️  Clicking buy button...
✅ TRADE EXECUTED SUCCESSFULLY
```

**No trade cycle:**
```
🔍 Scanning for active markets...
✅ Found 1 active markets
📈 Analyzing BTC price action...
   Signal: PASS | Confidence: 45%
💡 Signal: PASS | Confidence: 45% | Reason: Confidence too low
⏸️  No trade signal or confidence too low
⏸️  Waiting 60 seconds until next check...
```

## Logs

**trades_log.jsonl** example:
```json
{"timestamp": "2026-01-28T15:45:30", "direction": "UP", "amount": 10.0, "status": "SUCCESS", "trades_count": 1, "capital_remaining": 290.0}
{"timestamp": "2026-01-28T16:02:15", "direction": "DOWN", "amount": 10.0, "status": "SUCCESS", "trades_count": 2, "capital_remaining": 280.0}
```

## Next Steps

Once stable:
- Run on Replit for 24/7 operation
- Increase position size gradually ($10 → $15 → $20)
- Add WhatsApp notifications via `notify_whatsapp.py`
- Track P&L and win rate
