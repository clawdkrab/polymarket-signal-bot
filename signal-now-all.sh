#!/bin/bash
#
# SIGNAL NOW - Show current signals for all 4 assets (single snapshot)
#

cd "$(dirname "$0")"

if [ ! -f signals_all.json ]; then
    echo "❌ No signals file found. Is multi-asset engine running?"
    exit 1
fi

python3 << 'PYEOF'
import json
from datetime import datetime

with open('signals_all.json', 'r') as f:
    data = json.load(f)

timestamp = data.get('timestamp', '')
time_str = timestamp[11:19] if len(timestamp) > 19 else 'N/A'
assets = data.get('assets', {})

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"📊 POLYMARKET 15M SIGNALS - {time_str} UTC")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

strong_signals = []

for asset_name in ['BTC', 'ETH', 'SOL', 'XRP']:
    asset = assets.get(asset_name, {})
    direction = asset.get('direction', 'UNKNOWN')
    confidence = asset.get('confidence', 0)
    price = asset.get('price', 0)
    basis = asset.get('basis', {})
    
    # Emoji
    if direction == 'UP':
        emoji = '🟢'
        action = 'BUY UP'
    elif direction == 'DOWN':
        emoji = '🔴'
        action = 'BUY DOWN'
    else:
        emoji = '⚪'
        action = 'PASS'
    
    print(f"\n{emoji} {asset_name} - {direction}")
    print(f"   Confidence: {confidence}%")
    print(f"   Price:      ${price:,.2f}")
    
    if confidence > 0:
        print(f"   Momentum:   30s: {basis.get('momentum_30s', 0):+.3f}%  |  2m: {basis.get('momentum_120s', 0):+.3f}%")
        print(f"   Trend:      {basis.get('trend_bias', 'N/A')}")
        print(f"   Score:      {basis.get('score', 0):+.3f}")
    
    # Recommendation
    if confidence >= 70 and direction != 'NO_TRADE':
        print(f"   💡 👉 STRONG {action}")
        strong_signals.append((asset_name, direction, confidence))
    elif confidence >= 60 and direction != 'NO_TRADE':
        print(f"   💡 Consider {action}")
    elif confidence > 0:
        print(f"   ⚠️  Weak signal - wait")
    else:
        print(f"   ⏸️  No trade")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if strong_signals:
    print(f"\n🎯 STRONG SIGNALS ({len(strong_signals)}/4):")
    for asset, direction, conf in strong_signals:
        print(f"   • {asset}: {direction} at {conf}%")
else:
    print("\n⏸️  No strong signals at this time - wait for next window")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
PYEOF
