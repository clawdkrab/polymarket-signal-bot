#!/usr/bin/env python3
"""
Polymarket Browser Automation
Trade 15-minute BTC markets via browser interaction
"""
import time
import re
from datetime import datetime
from typing import Optional, Dict, List


class PolymarketBrowser:
    """Browser automation for Polymarket trading."""
    
    def __init__(self, browser_tool):
        """
        Args:
            browser_tool: Clawdbot browser tool instance
        """
        self.browser = browser_tool
        self.base_url = "https://polymarket.com"
        self.logged_in = False
        
    def check_login_status(self) -> bool:
        """Check if wallet is connected."""
        print("🔍 Checking login status...")
        
        try:
            # Take snapshot to check for wallet connection
            snapshot = self.browser.snapshot()
            
            # Look for wallet address or connect button
            if "connect wallet" in snapshot.lower():
                print("⚠️  Wallet not connected")
                return False
            
            if "0x" in snapshot:  # Ethereum address pattern
                print("✅ Wallet appears to be connected")
                return True
                
            return False
            
        except Exception as e:
            print(f"⚠️  Could not check login: {e}")
            return False
    
    def navigate_to_btc_markets(self) -> bool:
        """Navigate to BTC Up/Down markets page."""
        print("🧭 Navigating to BTC markets...")
        
        try:
            # Go to main crypto page
            url = f"{self.base_url}/markets/crypto"
            self.browser.navigate(targetUrl=url)
            time.sleep(2)
            
            print("✅ At crypto markets page")
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def find_active_15min_markets(self) -> List[Dict]:
        """
        Find active 15-minute BTC Up/Down markets on the page.
        
        Returns:
            List of market dicts with: url, question, end_time, yes_price, no_price
        """
        print("🔍 Scanning for 15-minute markets...")
        
        try:
            snapshot = self.browser.snapshot()
            
            markets = []
            
            # Look for "Bitcoin Up or Down" or similar patterns
            lines = snapshot.split('\n')
            
            for i, line in enumerate(lines):
                # Look for BTC up/down markets
                if 'bitcoin' in line.lower() and ('up' in line.lower() or 'down' in line.lower()):
                    # Try to extract market info from surrounding lines
                    market_text = '\n'.join(lines[max(0, i-5):min(len(lines), i+10)])
                    
                    # Look for time indicators
                    time_match = re.search(r'(\d+):(\d+)', market_text)
                    
                    # Look for prices (0.XX format)
                    price_matches = re.findall(r'0\.\d+', market_text)
                    
                    if time_match and price_matches:
                        market = {
                            'question': line.strip(),
                            'text_block': market_text,
                            'prices': price_matches,
                            'raw_line': line
                        }
                        markets.append(market)
            
            print(f"{'✅' if markets else '⚠️ '} Found {len(markets)} potential markets")
            
            return markets
            
        except Exception as e:
            print(f"❌ Error scanning markets: {e}")
            return []
    
    def get_market_details(self, market_url: str) -> Optional[Dict]:
        """
        Navigate to a specific market and extract details.
        
        Args:
            market_url: Full URL to the market
            
        Returns:
            Dict with: question, end_time, price_to_beat, current_price, yes_odds, no_odds
        """
        print(f"📊 Getting market details...")
        
        try:
            self.browser.navigate(targetUrl=market_url)
            time.sleep(2)
            
            snapshot = self.browser.snapshot()
            
            # Extract key info
            details = {
                'url': market_url,
                'snapshot_text': snapshot[:500]
            }
            
            # Look for "price to beat"
            price_match = re.search(r'price to beat.*?\$([0-9,]+\.\d+)', snapshot, re.IGNORECASE | re.DOTALL)
            if price_match:
                details['price_to_beat'] = float(price_match.group(1).replace(',', ''))
            
            # Look for current price
            current_match = re.search(r'current price.*?\$([0-9,]+\.\d+)', snapshot, re.IGNORECASE | re.DOTALL)
            if current_match:
                details['current_price'] = float(current_match.group(1).replace(',', ''))
            
            # Look for YES/NO odds (typically shown as prices like 0.52)
            odds_matches = re.findall(r'(0\.\d{2})', snapshot)
            if len(odds_matches) >= 2:
                details['yes_odds'] = float(odds_matches[0])
                details['no_odds'] = float(odds_matches[1])
            
            # Look for time remaining
            time_match = re.search(r'(\d+)\s*min(?:s)?', snapshot)
            if time_match:
                details['minutes_remaining'] = int(time_match.group(1))
            
            print(f"✅ Extracted market details")
            return details
            
        except Exception as e:
            print(f"❌ Error getting details: {e}")
            return None
    
    def place_trade(self, direction: str, amount: float) -> bool:
        """
        Place a trade on the current market page.
        
        Args:
            direction: "UP" or "DOWN"
            amount: Dollar amount to trade
            
        Returns:
            True if trade placed successfully
        """
        print(f"\n{'='*60}")
        print(f"🚨 PLACING TRADE: {direction} for ${amount:.2f}")
        print(f"{'='*60}\n")
        
        try:
            # Take snapshot to find trade buttons
            snapshot = self.browser.snapshot()
            
            # Look for UP or DOWN button
            # This will depend on Polymarket's actual UI structure
            # We'll need to inspect and adjust
            
            # Click the appropriate button
            if direction.upper() == "UP":
                # Find and click UP/YES button
                print("🖱️  Clicking UP button...")
                # self.browser.click(selector='button:contains("Up")')
                pass
            else:
                # Find and click DOWN/NO button
                print("🖱️  Clicking DOWN button...")
                # self.browser.click(selector='button:contains("Down")')
                pass
            
            time.sleep(1)
            
            # Enter amount
            print(f"⌨️  Entering amount: ${amount:.2f}")
            # self.browser.type(selector='input[type="number"]', text=str(amount))
            
            time.sleep(1)
            
            # Click confirm/buy button
            print("🖱️  Clicking confirm...")
            # self.browser.click(selector='button:contains("Buy")')
            
            time.sleep(2)
            
            # Check for success confirmation
            snapshot_after = self.browser.snapshot()
            
            if "success" in snapshot_after.lower() or "confirmed" in snapshot_after.lower():
                print("✅ Trade placed successfully!")
                return True
            else:
                print("⚠️  Trade status unclear - check manually")
                return False
                
        except Exception as e:
            print(f"❌ Trade failed: {e}")
            return False
    
    def scan_for_opportunities(self) -> List[Dict]:
        """
        Scan for active 15-minute BTC markets.
        Returns list of market opportunities.
        """
        print("\n" + "="*60)
        print("🔍 SCANNING FOR 15-MIN BTC MARKETS")
        print("="*60 + "\n")
        
        # Navigate to markets page
        if not self.navigate_to_btc_markets():
            return []
        
        # Find active markets
        markets = self.find_active_15min_markets()
        
        return markets
