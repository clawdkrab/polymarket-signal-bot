#!/bin/bash
#
# WATCH ALL SIGNALS - Monitor all 4 Polymarket assets
# BTC, ETH, SOL, XRP
#

cd "$(dirname "$0")"

clear
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║          📊 POLYMARKET 15M SIGNALS - ALL 4 ASSETS                      ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to exit"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

show_signals() {
    if [ ! -f signals_all.json ]; then
        echo "⚠️  No signals file found. Starting engine..."
        return
    fi
    
    python3 << 'PYEOF'
import json
import sys

try:
    with open('signals_all.json', 'r') as f:
        data = json.load(f)
    
    timestamp = data.get('timestamp', '')
    time_str = timestamp[11:19] if len(timestamp) > 19 else 'N/A'
    assets = data.get('assets', {})
    
    # Clear previous display
    print('\033[H\033[J', end='')  # Clear screen
    
    from datetime import datetime
    
    # Activity indicator (rotates)
    indicators = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    indicator = indicators[int(datetime.now().timestamp()) % len(indicators)]
    
    print("╔════════════════════════════════════════════════════════════════════════╗")
    print("║          📊 POLYMARKET 15M SIGNALS - ALL 4 ASSETS                      ║")
    print("╚════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"{indicator} Live: {time_str} UTC                         Press Ctrl+C to exit")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for asset_name in ['BTC', 'ETH', 'SOL', 'XRP']:
        asset = assets.get(asset_name, {})
        direction = asset.get('direction', 'UNKNOWN')
        confidence = asset.get('confidence', 0)
        price = asset.get('price', 0)
        basis = asset.get('basis', {})
        
        # Emoji and color
        if direction == 'UP':
            emoji = '🟢'
            action = 'BUY UP'
            color = '\033[92m'
        elif direction == 'DOWN':
            emoji = '🔴'
            action = 'BUY DOWN'
            color = '\033[91m'
        else:
            emoji = '⚪'
            action = 'PASS'
            color = '\033[90m'
        
        reset = '\033[0m'
        
        # Asset header
        print(f"\n{emoji} {color}{asset_name:4s} {direction:8s}{reset} | Conf: {confidence:2d}% | ${price:>10,.2f}")
        
        # Always show technical details (even if NO_TRADE)
        mom_30s = basis.get('momentum_30s', 0)
        mom_120s = basis.get('momentum_120s', 0)
        trend = basis.get('trend_bias', 'unknown')
        score = basis.get('score', 0)
        print(f"   30s: {mom_30s:+.3f}% | 2m: {mom_120s:+.3f}% | Score: {score:+.2f} | Trend: {trend}")
        
        # Recommendation
        if confidence >= 70:
            print(f"   👉 {color}STRONG {action}{reset}")
        elif confidence >= 60:
            print(f"   💡 Consider {action}")
        elif confidence > 0:
            print(f"   ⚠️  Weak signal")
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Count strong signals
    strong_count = sum(1 for a in assets.values() if a.get('confidence', 0) >= 70 and a.get('direction') != 'NO_TRADE')
    if strong_count > 0:
        print(f"\n🎯 {strong_count} STRONG SIGNAL(S) - Ready to trade!")
    
    sys.stdout.flush()

except Exception as e:
    print(f"⚠️  Error: {e}")
    sys.stdout.flush()
PYEOF
}

# Continuous monitoring
while true; do
    show_signals
    sleep 3
done
