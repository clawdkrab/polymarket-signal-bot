#!/usr/bin/env python3
"""
Test Agent - Single Cycle
Run one analysis cycle without live trading.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import TradingAgent

def main():
    """Run a single test cycle."""
    print("🧪 AGENT TEST MODE")
    print("Running single analysis cycle (no live trading)")
    print()
    
    agent = TradingAgent(capital=100.0)
    
    # Run one cycle
    agent.run_cycle()
    
    print()
    print("✅ Test complete!")
    print()
    print("To run autonomous mode:")
    print("  python3 main.py")

if __name__ == "__main__":
    main()
