#!/usr/bin/env python3
"""
Test script to find updown 15-min markets
Run this in Replit with your API credentials
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.polymarket_client import PolymarketClient

# Load credentials from environment
creds = {
    'api_key': os.getenv('POLYMARKET_API_KEY'),
    'secret': os.getenv('POLYMARKET_SECRET'),
    'passphrase': os.getenv('POLYMARKET_PASSPHRASE')
}

if not all(creds.values()):
    print("❌ Missing API credentials in environment!")
    sys.exit(1)

print("🔍 Testing authenticated API access...\n")

client = PolymarketClient(credentials=creds)

# Get all active markets
print("Fetching all active markets...")
markets = client.get_markets(limit=500, closed=False)
print(f"✅ Found {len(markets)} total active markets\n")

# Look for updown markets
updown = []
for m in markets:
    slug = m.get('slug', '')
    question = m.get('question', '').lower()
    
    if 'updown' in slug or 'up-down' in slug:
        updown.append(m)

print(f"{'✅' if updown else '❌'} Found {len(updown)} 'updown' markets\n")

if updown:
    print("Found updown markets:")
    for m in updown[:10]:
        print(f"  📊 {m.get('question')}")
        print(f"     Slug: {m.get('slug')}")
        print(f"     Volume: ${float(m.get('volume', 0)):,.0f}")
        print(f"     Active: {m.get('active')} | Closed: {m.get('closed')}")
        print()
else:
    print("No updown markets found in API response.")
    print("\nSearching for any BTC/Bitcoin markets:")
    btc = [m for m in markets if 'btc' in m.get('question', '').lower() or 'bitcoin' in m.get('question', '').lower()]
    print(f"  Found {len(btc)} BTC markets")
    for m in btc[:5]:
        print(f"    - {m.get('question')}")
