# 🤖 Polymarket BTC Trading Agent

**Autonomous trading agent for Bitcoin 15-minute Up/Down markets on Polymarket.**

## 🎯 Objective

Maximize net profit over a rolling 24-hour window while preserving capital. **Survival is mandatory. Blowing up is failure.**

## 📊 Trading Universe

- **Asset:** Bitcoin only
- **Market Type:** Polymarket BTC 15-minute Up/Down resolution markets
- **Timeframe:** 15-minute candles
- **Capital:** $100 starting balance (currently ~$300 funded)

## 🧠 Core Principles

1. **Trade conservatively** when signal confidence is low
2. **Increase position size** only when multiple independent signals align
3. **Never risk more** than is rational for capital preservation
4. **Treat this capital as irreplaceable**

## 📈 Data Inputs

- Recent BTC price data (last 50-100 resolved 15m markets)
- Momentum and volatility patterns
- Simple technical indicators (RSI, short-term MAs, trend strength)
- Real-time public sentiment from X (Twitter)
  - Sudden narrative shifts
  - Political/macro headlines
  - High-engagement posts affecting BTC sentiment
  - Market reaction speed after news

## 🎲 Decision Framework

- Identify momentum continuation vs exhaustion
- Avoid chop unless probability edge is clear
- Prioritize high-conviction setups over frequency
- Compound gains progressively when win-rate confirms edge
- Reduce size immediately after drawdowns

## ⚡ Execution Rules

Every trade must include:
- **Direction:** UP or DOWN
- **Position size:** Dynamic based on confidence
- **Reasoning:** Concise, factual, no storytelling
- **Confidence score:** 0-100%

**Do not trade if no clear edge exists.** Sitting out is a valid and often optimal decision.

## 🛡️ Risk Management

- Capital protection overrides profit seeking
- If conditions become unclear or regime shifts occur, reduce exposure
- Never revenge trade
- Adapt position sizing dynamically based on recent performance

## 📝 Self-Review

After each trade, log:
- Outcome
- Whether the thesis played out
- What signal mattered most

Periodically reflect on:
- What worked
- What failed
- What should be adjusted going forward

## 🏗️ Project Structure

```
polymarket-btc-agent/
├── src/
│   ├── data/
│   │   └── polymarket_client.py    # API integration
│   ├── indicators/                 # (TODO) Technical indicators
│   ├── trading/                    # (TODO) Strategy & risk mgmt
│   ├── memory/                     # Trade logs & performance data
│   │   ├── trades.jsonl           # All executed trades
│   │   └── performance.json        # Running stats
│   └── agent.py                    # Main autonomous loop
├── main.py                         # Entry point
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Setup

```bash
cd ~/clawd/polymarket-btc-agent
pip3 install requests pandas numpy python-dotenv

# Credentials stored in ~/.polymarket_credentials.json
```

### Run

```bash
python3 main.py
```

The agent will:
1. Search for active BTC 15-min markets
2. Analyze each market for trading opportunities  
3. Execute trades when high-confidence signals appear
4. Log all decisions and track performance
5. Repeat every 60 seconds

### Stop

Press `Ctrl+C` to stop the agent gracefully.

## 📦 API Integration

Uses Polymarket REST APIs:
- **CLOB API:** Order management, prices, orderbooks
- **Gamma API:** Market discovery and metadata
- **Data API:** Positions and trade history

Authentication: L2 HMAC-SHA256 signatures

## 🔒 Security

- API credentials stored in `~/.polymarket_credentials.json`
- Credentials never committed to git (`.gitignore`)
- All trading activity is non-custodial (wallet-based)

## 📊 Current Status

### ✅ Implemented
- Polymarket API client (CLOB + Gamma)
- Autonomous trading loop
- Market discovery (BTC 15-min markets)
- Trade logging and performance tracking
- State persistence

### 🚧 TODO
- **Strategy logic** (currently conservative - always PASS)
- Technical indicators (RSI, MAs, momentum)
- Sentiment analysis (Twitter/X integration)
- Position sizing algorithm
- Risk management rules
- Order execution (place/cancel orders)
- Backtest framework

## 🎯 Next Steps

1. **Implement strategy logic** in `src/agent.py:analyze_market()`
2. **Add technical indicators** in `src/indicators/`
3. **Build sentiment analyzer** in `src/data/sentiment.py`
4. **Add order execution** in `src/agent.py:execute_trade()`
5. **Test with paper trading** before going live

## 🧪 Testing

Currently in **observation mode** - analyzes markets but doesn't place real orders yet.

To enable live trading:
1. Complete strategy implementation
2. Test thoroughly
3. Uncomment order execution code in `execute_trade()`

## 📚 Resources

- [Polymarket CLOB Docs](https://docs.polymarket.com/developers/CLOB/introduction)
- [Gamma API Docs](https://docs.polymarket.com/developers/gamma-markets-api/overview)
- [Market Discovery](https://docs.polymarket.com/developers/gamma-markets-api/get-markets)

## ⚠️ Disclaimer

This bot trades real money. Only run it if you:
- Understand the risks
- Can afford to lose the capital
- Have thoroughly tested the strategy

**Past performance does not guarantee future results.**

---

**Status:** 🟡 In Development | **Last Update:** 2026-01-27
