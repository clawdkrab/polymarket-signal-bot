#!/bin/bash
#
# QUICK START SCRIPT FOR POLYMARKET BTC AGENT
# Sets correct environment variables and starts the bot
#

set -e

cd "$(dirname "$0")"

# Configuration
export CHROME_PROFILE="Profile 1"      # Polymarket Bot profile
export POSITION_SIZE=10.0              # Trade size in USD
export CONFIDENCE=60                   # Minimum confidence threshold

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 POLYMARKET BTC AGENT - QUICK START"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Profile:     $CHROME_PROFILE (polymarketv2@gmail.com)"
echo "Position:    \$$POSITION_SIZE per trade"
echo "Confidence:  $CONFIDENCE% minimum"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Chrome is running
if ps aux | grep -i "Google Chrome" | grep -v grep > /dev/null 2>&1; then
    echo "⚠️  Chrome is currently running."
    echo "   The bot needs exclusive access to the profile."
    echo ""
    read -p "   Close Chrome and continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled by user"
        exit 1
    fi
    
    echo "🔴 Closing Chrome..."
    pkill -9 -x "Google Chrome" 2>/dev/null || true
    sleep 2
    echo "✅ Chrome closed"
    echo ""
fi

# Start the bot
./supervisor.sh start

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BOT IS NOW RUNNING 24/7"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Monitor with:"
echo "  ./supervisor.sh logs        # Live logs"
echo "  tail -f trades.jsonl        # Watch trades"
echo "  ./supervisor.sh status      # System status"
echo ""
echo "Stop with:"
echo "  ./supervisor.sh stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
