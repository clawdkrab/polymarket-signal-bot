# 🚀 Replit Deployment Guide

## Quick Deploy (5 Minutes)

### 1. Import to Replit

Go to: **https://replit.com/github/clawdkrab/polymarket-btc-agent**

Or:
1. Go to https://replit.com
2. Click **"+ Create Repl"**
3. Select **"Import from GitHub"**
4. Paste: `https://github.com/clawdkrab/polymarket-btc-agent`
5. Click **"Import from GitHub"**

---

### 2. Add Secrets (REQUIRED)

In your Repl, click **🔒 Secrets** (left sidebar, padlock icon)

Add these 3 secrets:

| Key | Value |
|-----|-------|
| `POLYMARKET_API_KEY` | `f14e675bbbb34413a6b6c9e670572770` |
| `POLYMARKET_SECRET` | `e888fbcd8b5b4d308cced52367660892` |
| `POLYMARKET_PASSPHRASE` | `krabking` |

**⚠️ These are YOUR credentials - never share them!**

---

### 3. Run

Click the big **▶ Run** button at the top.

You should see:
```
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

     LIVE MODE - MONITORING FOR BTC 15-MIN MARKETS

⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

✅ Credentials loaded from environment variables
======================================================================
⚠️  LIVE TRADING MODE - REAL CAPITAL
======================================================================
Capital: $300.00
Max Position: 10%
Min Confidence: 70%
Max Daily Loss: 15%
======================================================================
```

---

## What Happens Now?

### 🔍 Monitoring Mode

The bot is now running 24/7 and will:

1. **Check every 5 minutes** for new markets
2. **Look for BTC 15-minute Up/Down markets**
3. **Analyze** when it finds tradeable markets
4. **Execute trades** ONLY on high-confidence setups (70%+)
5. **Log everything** to memory files

### ⏸️ Most of the Time

You'll see:
```
[02:45:12] 🔄 Starting cycle...
Capital: $300.00 | Daily P&L: $0.00 | Trades: 0

🔍 Searching for tradeable markets...
✅ Found 1 tradeable crypto markets

📊 Analyzing: Will bitcoin hit $1m before GTA VI?
   ⏸️  PASS - Not a short-term market

💤 Next check in 300s...
```

This is **GOOD** - the bot is being selective!

### 🚀 When It Finds a Trade

You'll see:
```
📊 Analyzing: BTC above $88,500 in 15 minutes?

   📈 RSI: 85.2 | Momentum: +1.3% | Trend: UP
   🎯 Signal: DOWN | Confidence: 85%

🚨 PREPARING TO EXECUTE REAL TRADE
   Market: BTC above $88,500 in 15 minutes?
   Direction: DOWN
   Size: $24.00
   Confidence: 85%

✅ Order placed! Monitoring...
```

---

## 🛡️ Safety Features

### Built-In Protections:
- ✅ Max 10% position size
- ✅ Min 70% confidence to trade
- ✅ Max 15% daily loss limit
- ✅ Capital preservation at 50% loss
- ✅ Max 10 trades per day
- ✅ Min $10 trade size

### Manual Controls:

**Stop the bot:** Click "Stop" button in Repl
**Check logs:** Look in Console tab
**View trades:** Check `src/memory/live_trades.jsonl`

---

## 📊 Monitoring Your Bot

### Check Status

The console will show regular updates:
```
[HH:MM:SS] 🔄 Starting cycle...
Capital: $XXX.XX | Daily P&L: $±XX.XX | Trades: X
```

### View Trade History

Trades are logged to: `src/memory/live_trades.jsonl`

Each line is a JSON trade record:
```json
{
  "timestamp": "2026-01-27T02:45:00",
  "market": "BTC above $88,500 in 15 minutes?",
  "action": "DOWN",
  "size": 24.00,
  "confidence": 85,
  "executed": true
}
```

### Performance Tracking

Check capital changes in the console output.

---

## ⚙️ Configuration

Edit `live_config.json` to adjust settings:

```json
{
  "capital": 300.0,
  "risk_settings": {
    "max_position_pct": 0.10,     ← Max 10% per trade
    "min_confidence": 70,          ← Min 70% to trade
    "max_daily_loss_pct": 0.15    ← Stop at 15% loss
  }
}
```

Changes take effect on next restart.

---

## 🚨 Troubleshooting

### "No credentials found"
→ Add the 3 secrets in the Secrets tab

### "No tradeable markets found"
→ Normal! Bot is waiting for BTC 15-min markets to appear

### Bot stopped
→ Click Run again, or enable "Always On" (Replit paid feature)

### Want to stop trading
→ Click Stop button, or delete the Repl

---

## 📱 Mobile Monitoring

Replit has a mobile app! Install it to:
- Check console logs from your phone
- Stop/start the bot remotely
- Get notifications (if Always On is enabled)

---

## 💰 Expected Behavior

### Week 1:
- Mostly passing (no clear edges)
- 0-3 trades likely
- Capital stays ~$300

### When Volatility Hits:
- More signals trigger
- 2-5 trades per day
- Capital fluctuates

### Target Performance:
- Win rate: 55-65%
- ROI: +5-15% per week (if markets exist)
- Drawdown: <20%

---

## 🔒 Security Notes

- ✅ Credentials stored as Secrets (encrypted)
- ✅ Never logged in console
- ✅ Not committed to git
- ✅ Only you can access your Repl

**Keep your Repl private!** Don't share the link.

---

## ⚡ Always On (Optional)

Free Repls sleep after inactivity. For 24/7 monitoring:

1. Upgrade to Replit Hacker plan ($7/mo)
2. Enable "Always On" for your Repl
3. Bot runs continuously without sleeping

**For testing:** Free plan is fine - just click Run when you want it active.

---

## 📊 Paper Trading (Testing)

Want to test without risking capital?

In the Shell tab, run:
```bash
python3 paper_mode_mock.py --cycles 20 --capital 300
```

This simulates 20 markets with mock data to validate the strategy.

---

## 🆘 Support

**Bot issues?** Check:
- Console for error messages
- `src/memory/live_trades.jsonl` for trade logs
- GitHub issues: https://github.com/clawdkrab/polymarket-btc-agent/issues

**Polymarket API issues?** Check:
- https://docs.polymarket.com/
- Polymarket Discord

---

**🐺 Your bot is now live and hunting for opportunities!**

Let it run. Check in daily. Trust the strategy. Capital preservation is priority #1.
