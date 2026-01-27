#!/usr/bin/env python3
"""
WhatsApp Trade Notifier
Monitors trade log and sends WhatsApp alerts when new trades happen
"""
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

TRADE_LOG = Path(__file__).parent / "src" / "memory" / "live_trades.jsonl"
STATE_FILE = Path(__file__).parent / "src" / "memory" / "notifier_state.json"

def load_last_notified():
    """Load the last notified trade timestamp."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f).get('last_notified', None)
    return None

def save_last_notified(timestamp):
    """Save the last notified trade timestamp."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_notified': timestamp}, f)

def send_whatsapp(message):
    """Send WhatsApp message via clawdbot."""
    try:
        result = subprocess.run([
            "clawdbot", "message", "send",
            "--channel", "whatsapp",
            "--target", "+7304002106",
            "--message", message
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ WhatsApp sent: {message[:50]}...")
            return True
        else:
            print(f"❌ Failed to send: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error sending WhatsApp: {e}")
        return False

def check_for_new_trades():
    """Check for new trades and notify."""
    if not TRADE_LOG.exists():
        return
    
    last_notified = load_last_notified()
    
    with open(TRADE_LOG, 'r') as f:
        for line in f:
            trade = json.loads(line)
            timestamp = trade.get('timestamp')
            
            # Skip if already notified
            if last_notified and timestamp <= last_notified:
                continue
            
            # New trade found!
            action = trade.get('action', 'UNKNOWN')
            size = trade.get('size', 0)
            confidence = trade.get('confidence', 0)
            rsi = trade.get('rsi', 0)
            
            # Format message
            emoji = "🟢" if action == "UP" else "🔴"
            message = f"""
{emoji} POLYMARKET TRADE EXECUTED!

Action: {action}
Size: ${size:.2f}
Confidence: {confidence}%
RSI: {rsi:.1f}

Time: {datetime.fromisoformat(timestamp).strftime('%H:%M:%S')}
            """.strip()
            
            # Send notification
            if send_whatsapp(message):
                save_last_notified(timestamp)

def monitor_continuous():
    """Monitor continuously for new trades."""
    print("🔔 WhatsApp Trade Notifier Started")
    print(f"📂 Monitoring: {TRADE_LOG}")
    print(f"📱 Target: +7304002106 (WhatsApp)")
    print("⏱️  Checking every 30 seconds")
    print()
    
    while True:
        try:
            check_for_new_trades()
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n⛔ Notifier stopped")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_continuous()
