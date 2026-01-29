#!/bin/bash
# Run signal bot + autonomous executor together

echo "=========================================="
echo "🚀 POLYMARKET AUTONOMOUS SYSTEM"
echo "=========================================="
echo ""

# Install playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "📦 Installing Playwright browsers (first run)..."
    playwright install chromium
    echo ""
fi

# Kill existing processes
pkill -f signal_bot_rest.py
pkill -f autonomous_executor.py

# Start signal bot in background
echo "📊 Starting signal generator..."
python3 signal_bot_rest.py > signal_bot.log 2>&1 &
SIGNAL_PID=$!
echo "   PID: $SIGNAL_PID"

# Wait for initial signals
echo "   Waiting for initial signals..."
sleep 10

# Check if signal file exists
if [ ! -f "latest_signals.json" ]; then
    echo "❌ Signal bot failed to start"
    kill $SIGNAL_PID
    exit 1
fi

echo "✅ Signal bot running"
echo ""

# Start autonomous executor
echo "🤖 Starting autonomous executor..."
python3 autonomous_executor.py

# Cleanup on exit
trap "kill $SIGNAL_PID" EXIT
