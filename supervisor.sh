#!/bin/bash
#
# SUPERVISOR - Keep polymarket-btc-agent running 24/7
# This script ensures both signal engine and trade executor stay alive
# independent of chat or terminal sessions.
#

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

SIGNAL_ENGINE="continuous_signal_engine.py"
TRADE_EXECUTOR="autonomous_trade_executor.py"

SIGNAL_LOG="signal_engine.log"
TRADE_LOG="trade_executor.log"

POSITION_SIZE="${POSITION_SIZE:-10.0}"
CONFIDENCE="${CONFIDENCE:-60}"

echo "=================================="
echo "🤖 POLYMARKET BTC AGENT SUPERVISOR"
echo "=================================="
echo "Repository: $REPO_DIR"
echo "Position size: \$$POSITION_SIZE"
echo "Confidence threshold: $CONFIDENCE%"
echo "Chrome profile: Polymarket Bot [HARD-CODED]"
echo "=================================="
echo ""

# Function to check if process is running
is_running() {
    local script_name="$1"
    ps aux | grep -F "$script_name" | grep -v grep > /dev/null 2>&1
}

# Function to start signal engine
start_signal_engine() {
    if is_running "$SIGNAL_ENGINE"; then
        echo "✅ Signal engine already running"
    else
        echo "🚀 Starting signal engine..."
        nohup python3 -u "$SIGNAL_ENGINE" > "$SIGNAL_LOG" 2>&1 &
        sleep 2
        
        if is_running "$SIGNAL_ENGINE"; then
            echo "✅ Signal engine started (PID: $(ps aux | grep -F "$SIGNAL_ENGINE" | grep -v grep | awk '{print $2}' | head -1))"
        else
            echo "❌ Signal engine failed to start"
            return 1
        fi
    fi
}

# Function to start trade executor
start_trade_executor() {
    if is_running "$TRADE_EXECUTOR"; then
        echo "✅ Trade executor already running"
    else
        # Check if Chrome is already running
        if ps aux | grep -i "Google Chrome" | grep -v grep > /dev/null 2>&1; then
            echo "⚠️  WARNING: Chrome is already running!"
            echo "   Playwright needs exclusive access to the profile."
            echo "   Close Chrome and try again, or press Enter to continue anyway..."
            read -t 5 || true
        fi
        
        echo "🚀 Starting trade executor..."
        nohup python3 -u "$TRADE_EXECUTOR" \
            --position-size "$POSITION_SIZE" \
            --confidence "$CONFIDENCE" \
            > "$TRADE_LOG" 2>&1 &
        sleep 2
        
        if is_running "$TRADE_EXECUTOR"; then
            echo "✅ Trade executor started (PID: $(ps aux | grep -F "$TRADE_EXECUTOR" | grep -v grep | awk '{print $2}' | head -1))"
        else
            echo "❌ Trade executor failed to start"
            echo "   Check: tail -50 $TRADE_LOG"
            return 1
        fi
    fi
}

# Function to stop all processes
stop_all() {
    echo "🛑 Stopping all processes..."
    
    if is_running "$SIGNAL_ENGINE"; then
        ps aux | grep -F "$SIGNAL_ENGINE" | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
        echo "   ✅ Signal engine stopped"
    fi
    
    if is_running "$TRADE_EXECUTOR"; then
        ps aux | grep -F "$TRADE_EXECUTOR" | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
        echo "   ✅ Trade executor stopped"
    fi
    
    echo "✅ All processes stopped"
}

# Function to show status
show_status() {
    echo "📊 System Status"
    echo "=================================="
    
    if is_running "$SIGNAL_ENGINE"; then
        local pid=$(ps aux | grep -F "$SIGNAL_ENGINE" | grep -v grep | awk '{print $2}' | head -1)
        echo "Signal Engine:  ✅ RUNNING (PID: $pid)"
    else
        echo "Signal Engine:  ❌ STOPPED"
    fi
    
    if is_running "$TRADE_EXECUTOR"; then
        local pid=$(ps aux | grep -F "$TRADE_EXECUTOR" | grep -v grep | awk '{print $2}' | head -1)
        echo "Trade Executor: ✅ RUNNING (PID: $pid)"
    else
        echo "Trade Executor: ❌ STOPPED"
    fi
    
    echo "=================================="
    
    # Show recent signal
    if [ -f "signal.json" ]; then
        echo ""
        echo "📡 Current Signal:"
        cat signal.json | python3 -m json.tool 2>/dev/null || cat signal.json
    fi
    
    # Show trade count
    if [ -f "trades.jsonl" ]; then
        local trade_count=$(wc -l < trades.jsonl)
        echo ""
        echo "📊 Trades executed: $trade_count"
    fi
}

# Function to tail logs
tail_logs() {
    echo "📜 Tailing logs (Ctrl+C to stop)..."
    echo ""
    tail -f "$SIGNAL_LOG" "$TRADE_LOG" 2>/dev/null
}

# Function to restart all
restart_all() {
    echo "♻️  Restarting all processes..."
    stop_all
    sleep 2
    start_signal_engine
    start_trade_executor
    echo "✅ Restart complete"
}

# Parse command
case "${1:-start}" in
    start)
        echo "🚀 Starting system..."
        start_signal_engine
        start_trade_executor
        echo ""
        show_status
        echo ""
        echo "✅ System started successfully!"
        echo ""
        echo "Useful commands:"
        echo "  ./supervisor.sh status    - Check system status"
        echo "  ./supervisor.sh stop      - Stop all processes"
        echo "  ./supervisor.sh restart   - Restart all processes"
        echo "  ./supervisor.sh logs      - Tail log files"
        ;;
    
    stop)
        stop_all
        ;;
    
    restart)
        restart_all
        ;;
    
    status)
        show_status
        ;;
    
    logs)
        tail_logs
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
