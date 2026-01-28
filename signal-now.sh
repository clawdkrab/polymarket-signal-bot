#!/bin/bash
#
# SIGNAL NOW - Show current signal (single snapshot)
#

cd "$(dirname "$0")"

if [ ! -f signal.json ]; then
    echo "❌ No signal file found. Is signal engine running?"
    exit 1
fi

python3 << 'PYEOF'
import json
from datetime import datetime

with open('signal.json', 'r') as f:
    signal = json.load(f)

# Extract data
timestamp = signal.get('timestamp', '')
direction = signal.get('direction', 'UNKNOWN')
confidence = signal.get('confidence', 0)
price = signal.get('price', 0)
basis = signal.get('basis', {})

# Parse timestamp
time_str = timestamp[11:19] if len(timestamp) > 19 else 'N/A'

# Direction emoji
if direction == 'UP':
    emoji = '🟢'
    action = 'BUY UP'
elif direction == 'DOWN':
    emoji = '🔴'
    action = 'BUY DOWN'
else:
    emoji = '⚪'
    action = 'PASS'

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"📊 BTC 15M SIGNAL - {time_str} UTC")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"\n{emoji} Direction:  {direction}")
print(f"   Confidence: {confidence}%")
print(f"   BTC Price:  ${price:,.2f}")

if confidence > 0:
    print(f"\n📈 Technical Basis:")
    print(f"   Momentum 30s:  {basis.get('momentum_30s', 0):+.3f}%")
    print(f"   Momentum 60s:  {basis.get('momentum_60s', 0):+.3f}%")
    print(f"   Momentum 120s: {basis.get('momentum_120s', 0):+.3f}%")
    print(f"   Volatility:    {basis.get('volatility_pct', 0):.3f}% ({basis.get('volatility_state', 'N/A')})")
    print(f"   Trend Bias:    {basis.get('trend_bias', 'N/A')}")
    print(f"   Score:         {basis.get('score', 0):+.3f}")

print(f"\n💡 Recommendation:")
if confidence >= 70:
    print(f"   👉 STRONG {action} - High confidence")
elif confidence >= 60:
    print(f"   💡 Consider {action} - Moderate confidence")
elif confidence >= 50:
    print(f"   ⚠️  Weak signal - Wait for better setup")
else:
    print(f"   ⏸️  PASS - No trade recommendation")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
PYEOF
