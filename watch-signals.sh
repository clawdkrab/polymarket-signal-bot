#!/bin/bash
#
# SIGNAL MONITOR - Clean display for manual trading
# Shows current signal in real-time with clear trade recommendations
#

cd "$(dirname "$0")"

# Clear screen and show header
clear
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║              📊 BTC 15M SIGNAL MONITOR - MANUAL TRADING                ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to exit"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to format signal display
show_signal() {
    if [ ! -f signal.json ]; then
        echo "⚠️  No signal file found. Starting signal engine..."
        return
    fi
    
    python3 << 'PYEOF'
import json
import sys
from datetime import datetime

try:
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
    
    # Direction emoji and color
    if direction == 'UP':
        emoji = '🟢'
        action = 'BUY UP'
        color = '\033[92m'  # Green
    elif direction == 'DOWN':
        emoji = '🔴'
        action = 'BUY DOWN'
        color = '\033[91m'  # Red
    else:
        emoji = '⚪'
        action = 'NO TRADE'
        color = '\033[90m'  # Gray
    
    reset = '\033[0m'
    
    # Clear previous signal (move cursor up)
    print('\033[2K', end='')  # Clear line
    
    # Print signal
    print(f"\r[{time_str}] {emoji} {color}{direction:8s}{reset} | Conf: {confidence:2d}% | ${price:,.0f}", end='')
    
    # Show basis details on same line if confidence > 0
    if confidence > 0:
        mom_30s = basis.get('momentum_30s', 0)
        mom_120s = basis.get('momentum_120s', 0)
        vol = basis.get('volatility_pct', 0)
        trend = basis.get('trend_bias', 'unknown')
        
        print(f" | 30s: {mom_30s:+.3f}% | 2m: {mom_120s:+.3f}% | Vol: {vol:.3f} | Trend: {trend.upper()}", end='')
    
    # Recommendation
    if confidence >= 70:
        print(f"\n   👉 {color}STRONG {action}{reset} - High confidence signal")
    elif confidence >= 60:
        print(f"\n   💡 Consider {action} - Moderate confidence")
    elif confidence >= 50:
        print(f"\n   ⚠️  Weak signal - Monitor for improvement")
    else:
        print(f"\n   ⏸️  No trade recommendation")
    
    sys.stdout.flush()

except Exception as e:
    print(f"\r⚠️  Error reading signal: {e}", end='')
    sys.stdout.flush()
PYEOF
}

# Continuous monitoring
while true; do
    show_signal
    sleep 3
done
