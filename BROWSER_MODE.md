# Browser Trading Mode

## Why Browser Mode?

The 15-minute "Bitcoin Up or Down" markets **are not available via Polymarket's REST API**. Browser mode uses Playwright to actually interact with the website, just like you do manually.

## Setup (Replit)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

2. **Connect your wallet:**
   - Open Polymarket.com in your Replit webview
   - Connect your MetaMask/wallet
   - Keep the browser session active

3. **Run the browser agent:**
```bash
python browser_agent.py
```

## How It Works

1. **Opens browser** (visible window)
2. **Navigates to crypto markets** page
3. **Finds 15-minute BTC markets** 
4. **Analyzes BTC price action** (technical indicators)
5. **Generates trading signal** (UP or DOWN)
6. **Pauses for you to execute** manually (for now)

## Current Limitations

- **Manual execution required** - Bot generates signals but you click "Buy"
- **Why?** Automated wallet signing requires browser extension injection (complex)
- **Future:** Can be automated with MetaMask programmatic signing

## Safety

- ✅ Capital limits enforced
- ✅ Confidence thresholds checked
- ✅ Risk management active
- ✅ You see every trade before it executes

## Workflow

```
1. Bot finds market → "Bitcoin Up or Down - 3:45-4:00PM"
2. Bot analyzes BTC → "Signal: UP, Confidence: 78%"
3. Bot suggests trade → "Buy $30 worth of UP"
4. Browser opens market → You see it on screen
5. Bot pauses → "Press ENTER after you execute manually"
6. You click Buy manually → Confirm in MetaMask
7. Press ENTER → Bot continues monitoring
```

## Fully Automated Trading (Advanced)

To fully automate:
1. Use Playwright with MetaMask extension injection
2. Programmatically approve transactions
3. Handle wallet popups automatically

This requires additional setup. Current semi-manual mode is safer for initial testing.

## Troubleshooting

**"Playwright not installed"**
```bash
pip install playwright
playwright install chromium
```

**Browser won't open**
- Replit might not support GUI browsers in free tier
- Use local machine or VPS with display

**Can't find markets**
- Markets appear every 15 minutes
- Try refreshing or checking at :00, :15, :30, :45

**Wallet not connected**
- Connect manually before running bot
- Keep browser window open
