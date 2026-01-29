#!/usr/bin/env python3
"""
POLYMARKET AUTONOMOUS TRADE EXECUTOR
Reads signals from signal_bot and executes trades automatically
"""
import json
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SIGNAL_FILE = Path(__file__).parent / "latest_signals.json"
TRADE_LOG = Path(__file__).parent / "auto_trades.jsonl"

# Trading parameters
MIN_CONFIDENCE = 70  # Only trade signals >= 70% confidence
POSITION_SIZE = 10   # USD per trade
MAX_TRADES_PER_MARKET = 1  # Don't double-up on same market window

# Polymarket URLs
POLYMARKET_BASE = "https://polymarket.com"
POLYMARKET_15M = f"{POLYMARKET_BASE}/crypto/15M"

# State tracking
executed_trades = set()  # Track executed market windows to prevent duplicates

# ═══════════════════════════════════════════════════════════════════════════
# TRADE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def load_signals():
    """Load current signals from file."""
    if not SIGNAL_FILE.exists():
        return []
    
    try:
        with open(SIGNAL_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading signals: {e}")
        return []

def should_trade(signal: dict) -> bool:
    """Determine if we should trade this signal."""
    # Must be READY
    if not signal.get('ready', False):
        return False
    
    # Must meet confidence threshold
    if signal.get('confidence', 0) < MIN_CONFIDENCE:
        return False
    
    # Must have clear direction
    if signal.get('direction') == 'NO_TRADE':
        return False
    
    # Check if we already traded this market window
    trade_key = f"{signal['token']}_{signal['entry_window']}"
    if trade_key in executed_trades:
        return False
    
    return True

def find_market_on_page(page: Page, token: str, direction: str) -> bool:
    """
    Find and click the correct market on Polymarket.
    Returns True if market found and clicked.
    """
    try:
        # Look for token name in market cards
        market_selector = f"text=/{token}/i"
        
        # Wait for markets to load
        page.wait_for_selector("[data-testid='market-card']", timeout=10000)
        
        # Find all market cards
        markets = page.locator("[data-testid='market-card']").all()
        
        for market in markets:
            market_text = market.inner_text()
            
            # Check if this is the right token
            if token.upper() in market_text.upper():
                # Click the market
                market.click()
                time.sleep(2)
                
                # Now find and click the correct outcome (UP or DOWN)
                if direction == 'UP':
                    outcome_btn = page.locator("button:has-text('Up')")
                else:
                    outcome_btn = page.locator("button:has-text('Down')")
                
                if outcome_btn.count() > 0:
                    outcome_btn.first.click()
                    return True
        
        return False
    
    except Exception as e:
        print(f"⚠️  Error finding market: {e}")
        return False

def execute_trade(page: Page, signal: dict) -> dict:
    """
    Execute a trade on Polymarket.
    Returns trade result dict.
    """
    token = signal['token']
    direction = signal['direction']
    confidence = signal['confidence']
    entry_window = signal['entry_window']
    
    print(f"\n🎯 EXECUTING TRADE")
    print(f"   Token: {token}")
    print(f"   Direction: {direction}")
    print(f"   Confidence: {confidence}%")
    print(f"   Entry: {entry_window}")
    print(f"   Size: ${POSITION_SIZE}")
    
    trade_result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'token': token,
        'direction': direction,
        'confidence': confidence,
        'entry_window': entry_window,
        'position_size': POSITION_SIZE,
        'status': 'failed',
        'error': None
    }
    
    try:
        # Navigate to 15M markets
        print(f"   → Opening {POLYMARKET_15M}")
        page.goto(POLYMARKET_15M, wait_until='networkidle', timeout=30000)
        time.sleep(3)
        
        # Find and click the market
        print(f"   → Finding {token} market...")
        if not find_market_on_page(page, token, direction):
            trade_result['error'] = 'Market not found'
            print(f"   ❌ Market not found")
            return trade_result
        
        print(f"   → Market found, entering position size...")
        time.sleep(2)
        
        # Enter position size
        amount_input = page.locator("input[type='number']").first
        if amount_input.count() > 0:
            amount_input.fill(str(POSITION_SIZE))
            time.sleep(1)
        else:
            trade_result['error'] = 'Amount input not found'
            print(f"   ❌ Amount input not found")
            return trade_result
        
        # Click buy/place order button
        print(f"   → Placing order...")
        buy_btn = page.locator("button:has-text('Buy'), button:has-text('Place Order')").first
        
        if buy_btn.count() > 0:
            buy_btn.click()
            time.sleep(3)
            
            # Confirm if needed
            confirm_btn = page.locator("button:has-text('Confirm')").first
            if confirm_btn.count() > 0:
                confirm_btn.click()
                time.sleep(2)
            
            trade_result['status'] = 'executed'
            print(f"   ✅ TRADE EXECUTED")
            
            # Mark this market window as traded
            trade_key = f"{token}_{entry_window}"
            executed_trades.add(trade_key)
        else:
            trade_result['error'] = 'Buy button not found'
            print(f"   ❌ Buy button not found")
    
    except PlaywrightTimeout as e:
        trade_result['error'] = f'Timeout: {str(e)}'
        print(f"   ❌ Timeout: {e}")
    
    except Exception as e:
        trade_result['error'] = str(e)
        print(f"   ❌ Error: {e}")
    
    return trade_result

def log_trade(trade: dict):
    """Append trade to log file."""
    with open(TRADE_LOG, 'a') as f:
        f.write(json.dumps(trade) + '\n')

# ═══════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("="*80)
    print("🤖 POLYMARKET AUTONOMOUS EXECUTOR")
    print("="*80)
    print(f"Min Confidence: {MIN_CONFIDENCE}%")
    print(f"Position Size: ${POSITION_SIZE}")
    print(f"Signal Source: {SIGNAL_FILE}")
    print("="*80)
    print()
    
    # Check if signal file exists
    if not SIGNAL_FILE.exists():
        print(f"❌ Signal file not found: {SIGNAL_FILE}")
        print("   Make sure signal_bot_rest.py is running first!")
        return
    
    print("🚀 Starting autonomous executor...")
    print("   Watching for READY signals...")
    print()
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # headless=True for production
        context = browser.new_context()
        page = context.new_page()
        
        # Login to Polymarket (you'll need to do this manually first time)
        print("📱 Opening Polymarket - please ensure you're logged in...")
        page.goto(POLYMARKET_BASE)
        
        # Wait for user to login if needed
        input("   Press ENTER once you're logged in...")
        
        print("✅ Ready to execute trades")
        print()
        
        last_signal_check = 0
        
        try:
            while True:
                time.sleep(1)
                
                # Check signals every 5 seconds
                now = time.time()
                if now - last_signal_check < 5:
                    continue
                
                last_signal_check = now
                
                # Load current signals
                signals = load_signals()
                
                if not signals:
                    continue
                
                # Check each signal
                for signal in signals:
                    if should_trade(signal):
                        # Execute trade
                        trade_result = execute_trade(page, signal)
                        log_trade(trade_result)
                        
                        # Brief pause between trades
                        time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n🛑 Executor stopped by user")
        
        finally:
            browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
