# 🏆 Elite Autonomous Polymarket Trader

**The ultimate autonomous trading bot combining institutional-grade strategy with full automation.**

## 🌟 What Makes It Elite

This bot combines the **best features from all previous versions** into one powerful system:

### Core Features

✅ **Institutional Multi-Gate Strategy**
- Momentum deceleration analysis
- Volatility expansion detection
- Range extreme / VWAP deviation tracking
- Session-aware trading (London/NY sessions)
- Requires 2-3 gates to pass before trading

✅ **Advanced Risk Management**
- Dynamic position sizing based on confidence (3-10% of capital)
- Drawdown protection (reduces size when down 10%+)
- Daily loss limits (stops at 15% daily loss)
- Win/loss streak adjustment
- Capital preservation mode

✅ **Full Automation**
- MetaMask auto-confirm (no manual clicking!)
- Auto-refresh every 60 seconds
- Full page reload every 15 minutes
- Persistent browser session (stays logged in)
- Error recovery and retry logic

✅ **Capital Compounding**
- Tracks capital across sessions
- Position sizes grow with capital
- Saves state after each trade
- Performance tracking and reporting

✅ **Smart Trading**
- 5-minute cooldown between trades
- Session awareness (more aggressive during active hours)
- Volatility regime detection
- Confidence-based execution (min 70%)

✅ **Performance Monitoring**
- Trade logging (elite_trades.jsonl)
- Performance reports (performance.json)
- Win/loss streak tracking
- Daily P&L tracking

---

## 📊 How It Works

### Signal Generation Process

1. **Fetch BTC Price Data** (Binance API)
   - Gets last 4 hours of hourly prices
   - Estimates 15-minute intervals

2. **Multi-Gate Analysis**
   ```
   Gate 1: Momentum Deceleration
   - Detects when strong momentum is slowing (reversal setup)
   
   Gate 2: Volatility Expansion
   - Looks for volatility spike (move is real)
   
   Gate 3: Range Extreme or VWAP Deviation
   - Price at extreme end of range
   - Or significantly deviated from volume-weighted average
   ```

3. **Session & Volatility Check**
   - Active session (London/NY overlap) = Need 2/3 gates
   - Inactive session = Need 3/3 gates (stricter)
   - High volatility = Loosen requirements

4. **Risk Manager Approval**
   - Check daily loss limits
   - Check drawdown limits
   - Check capital preservation threshold
   - Calculate position size based on confidence + recent performance

5. **Execute if Confidence ≥ 70%**

### Position Sizing Logic

```python
Base Size = Capital × 3% × (Confidence / 100)

Adjustments:
- Win streak (2+): +20%
- Loss streak (2+): -50%
- Drawdown > 10%: -30%
- Drawdown > 20%: -50%

Final Size = Max(min_trade, Min(adjusted_size, capital × 10%))
```

**Example:**
- Capital: $300
- Confidence: 85%
- No streaks
- Result: $300 × 3% × 0.85 = **$7.65 position**

If on 3-win streak:
- $7.65 × 1.2 = **$9.18 position**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install playwright requests numpy
playwright install chromium
```

### 2. Setup Config (Optional)

Edit `live_config.json`:

```json
{
  "capital": 300.0,
  "risk_settings": {
    "max_position_pct": 0.10,
    "base_position_pct": 0.03,
    "min_confidence": 70,
    "max_daily_loss_pct": 0.15
  }
}
```

### 3. Run the Bot

```bash
# Normal mode (browser visible)
python3 elite_autonomous_trader.py

# Headless mode (background)
python3 elite_autonomous_trader.py --headless

# Custom config
python3 elite_autonomous_trader.py --config my_config.json
```

---

## 📈 Expected Performance

### Theoretical Edge

With **multi-gate confirmation** and **institutional strategy**:
- Win rate: 55-65% (vs 50% random)
- Average trade: $8-12 position size
- Trades per day: 3-8 (depending on volatility)

**Example Session:**
```
Starting Capital: $300
Confidence Threshold: 70%
Average Position: $10

Scenario (60% win rate, 8 trades/day):
- 5 wins × $5 profit = +$25
- 3 losses × $4.50 loss = -$13.50
- Net: +$11.50/day (+3.8%)

After 7 days: $300 → $324
After 30 days: $300 → $407 (compound)
```

**Risk Management Protects You:**
- Max drawdown: 20% ($60 from peak)
- Daily stop: 15% ($45 loss in one day)
- Position limits prevent catastrophic losses

---

## 🛡️ Safety Features

### What Can Go Wrong?

1. **Browser Issues**
   - ✅ Persistent session keeps login
   - ✅ Auto-retry on navigation errors
   - ✅ Graceful shutdown on fatal errors

2. **MetaMask Failures**
   - ✅ Detects popup windows
   - ✅ Auto-clicks confirm
   - ✅ Falls back to manual if needed
   - ✅ Logs uncertain trades for review

3. **Bad Streak**
   - ✅ Position size cuts 50% after 2 losses
   - ✅ Daily loss limit stops trading
   - ✅ Drawdown protection kicks in at -10%

4. **Market Conditions**
   - ✅ Requires 2-3 gates to pass (filters noise)
   - ✅ Session awareness (stricter at night)
   - ✅ Volatility regime detection
   - ✅ 5-min cooldown prevents overtrading

---

## 📊 Monitoring & Logs

### Trade Log (`elite_trades.jsonl`)

Each trade creates a JSON line:
```json
{
  "timestamp": "2026-01-28T16:45:23",
  "direction": "UP",
  "amount": 10.50,
  "status": "SUCCESS",
  "capital": 310.50,
  "trades_count": 5,
  "win_streak": 2,
  "loss_streak": 0
}
```

### Performance Report (`performance.json`)

Session summary:
```json
{
  "runtime_hours": 8.5,
  "initial_capital": 300.0,
  "final_capital": 324.50,
  "total_pnl": 24.50,
  "total_pnl_pct": 8.17,
  "trades_executed": 12
}
```

### Bot State (`src/memory/bot_state.json`)

Persistent state across restarts:
```json
{
  "capital": 324.50,
  "trades_today": 12,
  "daily_pnl": 24.50,
  "win_streak": 3,
  "loss_streak": 0
}
```

---

## 🔧 Customization

### Adjust Risk Profile

**Conservative (Safer):**
```json
{
  "risk_settings": {
    "base_position_pct": 0.02,  // 2% base
    "max_position_pct": 0.05,   // 5% max
    "min_confidence": 75         // Higher bar
  }
}
```

**Aggressive (Higher risk/reward):**
```json
{
  "risk_settings": {
    "base_position_pct": 0.05,  // 5% base
    "max_position_pct": 0.15,   // 15% max
    "min_confidence": 65         // Lower bar
  }
}
```

### Change Trading Frequency

Edit `elite_autonomous_trader.py`:

```python
self.cooldown_minutes = 3  # Faster (default: 5)
self.refresh_interval = 30  # Check every 30s (default: 60)
```

---

## 🎯 Pro Tips

1. **Start with small capital** ($100-300) to test
2. **Run for 24-48 hours** to see performance pattern
3. **Monitor the first few trades** manually
4. **Check logs daily** for any errors
5. **Increase capital gradually** as confidence grows
6. **Use headless mode** for 24/7 operation on server

### Deployment on Replit/VPS

```bash
# Clone repo
git clone https://github.com/clawdkrab/polymarket-btc-agent
cd polymarket-btc-agent

# Install
pip install -r requirements.txt
playwright install chromium

# Run in background
nohup python3 elite_autonomous_trader.py --headless > trader.log 2>&1 &

# Monitor
tail -f trader.log
```

---

## 🔍 Troubleshooting

### "Advanced modules not found"
```bash
# Ensure src/ directory exists
ls src/

# Check imports
python3 -c "from src.data.price_feed import BTCPriceFeed"
```

### "Browser launch failed"
```bash
# Reinstall Playwright
playwright install --force chromium

# Check permissions
ls -la ~/.polymarket_elite_browser
```

### "MetaMask not auto-confirming"
- Run in **non-headless** mode first
- Manually connect wallet once
- Ensure MetaMask extension is logged in
- Check popup blocker settings

### "No trades executing"
- Lower `min_confidence` in config (try 65%)
- Check if market is active (15M BTC market exists?)
- Review signal analysis output (are gates passing?)

---

## 📝 Version History

### v1.0 - Elite Trader (2026-01-28)
- ✅ Integrated institutional multi-gate strategy
- ✅ Added dynamic risk management
- ✅ Implemented capital compounding
- ✅ Enhanced error recovery
- ✅ Added performance tracking
- ✅ Session-aware trading
- ✅ MetaMask auto-confirm

**Built on:**
- `autonomous_15m_trader.py` (MetaMask automation)
- `institutional_strategy.py` (Multi-gate analysis)
- `risk_manager.py` (Position sizing)
- `automated_trader.py` (Capital tracking)

---

## ⚠️ Disclaimer

**This bot trades real money on Polymarket.**

- Not financial advice
- Use at your own risk
- Past performance ≠ future results
- Start small and test thoroughly
- Monitor regularly

**You are responsible for:**
- Capital allocation
- Risk management
- Legal compliance
- Tax reporting

---

## 🤝 Support

Issues or questions? Check:
- `MEMORY.md` for project history
- `trades_log.jsonl` for execution history
- `performance.json` for session stats

Built with ❤️ by Clawd (Clawdbot Autonomous Agent)
