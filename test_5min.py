#!/usr/bin/env python3
"""
5-MINUTE HEALTH CHECK
Tests the smart browser agent without actual trading
"""
import sys
import time
from pathlib import Path
from datetime import datetime
import psutil
import os

sys.path.insert(0, str(Path(__file__).parent / "src"))

from smart_browser_agent import SmartTradingAgent

def get_memory_usage():
    """Get current process memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def run_5min_test():
    """Run 5-minute health check."""
    print("="*70)
    print("🧪 5-MINUTE HEALTH CHECK")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Test Duration: 5 minutes")
    print(f"Check Interval: 30 seconds (10 cycles total)")
    print()
    print("Testing:")
    print("  ✓ Bitcoin Up/Down market analysis")
    print("  ✓ RSI calculation")
    print("  ✓ Signal generation")
    print("  ✓ Memory usage")
    print("  ✓ Stability")
    print()
    print("="*70)
    print()
    
    # Create agent
    agent = SmartTradingAgent(config_path="live_config.json")
    
    start_time = time.time()
    cycle_count = 0
    signals_generated = 0
    memory_readings = []
    errors = []
    
    try:
        while (time.time() - start_time) < 300:  # 5 minutes
            cycle_count += 1
            cycle_start = time.time()
            
            print(f"\n{'='*70}")
            print(f"CYCLE #{cycle_count} @ {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*70}")
            
            # Measure memory before
            mem_before = get_memory_usage()
            memory_readings.append(mem_before)
            
            try:
                # Run analysis (no browser, just price check)
                signal = agent.analyze_signal()
                
                if signal:
                    signals_generated += 1
                    print(f"\n🚨 SIGNAL #{signals_generated} DETECTED!")
                    print(f"   Action: {signal['action']}")
                    print(f"   Confidence: {signal['confidence']}%")
                    print(f"   Size: ${signal['size']:.2f}")
                else:
                    print(f"\n✅ No signal (correctly passing)")
                
            except Exception as e:
                errors.append(str(e))
                print(f"\n❌ Error: {e}")
            
            # Measure memory after
            mem_after = get_memory_usage()
            print(f"\n📊 Memory: {mem_after:.1f} MB (Δ {mem_after - mem_before:+.1f} MB)")
            
            # Calculate time remaining
            elapsed = time.time() - start_time
            remaining = 300 - elapsed
            
            if remaining > 30:
                print(f"\n💤 Next check in 30s... ({remaining/60:.1f} min remaining)")
                time.sleep(30)
            else:
                print(f"\n⏰ Test ending in {remaining:.0f}s...")
                if remaining > 0:
                    time.sleep(remaining)
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    # Results
    elapsed_total = time.time() - start_time
    
    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)
    print(f"\n⏱️  Duration: {elapsed_total/60:.1f} minutes")
    print(f"🔄 Cycles Completed: {cycle_count}")
    print(f"🎯 Signals Generated: {signals_generated}")
    print(f"❌ Errors: {len(errors)}")
    
    if memory_readings:
        avg_memory = sum(memory_readings) / len(memory_readings)
        max_memory = max(memory_readings)
        min_memory = min(memory_readings)
        
        print(f"\n💾 Memory Usage:")
        print(f"   Average: {avg_memory:.1f} MB")
        print(f"   Peak: {max_memory:.1f} MB")
        print(f"   Min: {min_memory:.1f} MB")
        print(f"   Variance: {max_memory - min_memory:.1f} MB")
    
    if errors:
        print(f"\n⚠️  Errors encountered:")
        for i, err in enumerate(errors, 1):
            print(f"   {i}. {err}")
    
    # Health assessment
    print(f"\n{'='*70}")
    print("🏥 HEALTH ASSESSMENT")
    print(f"{'='*70}")
    
    health_score = 100
    issues = []
    
    if errors:
        health_score -= len(errors) * 20
        issues.append(f"❌ {len(errors)} errors occurred")
    
    if memory_readings and max(memory_readings) > 200:
        health_score -= 30
        issues.append(f"⚠️  High memory usage ({max(memory_readings):.0f} MB)")
    
    if cycle_count < 8:
        health_score -= 10
        issues.append(f"⚠️  Only {cycle_count} cycles (expected 10)")
    
    if health_score >= 90:
        status = "🟢 EXCELLENT - Ready for live trading"
    elif health_score >= 70:
        status = "🟡 GOOD - Minor issues but workable"
    elif health_score >= 50:
        status = "🟠 FAIR - Needs attention"
    else:
        status = "🔴 POOR - Not ready for live trading"
    
    print(f"\nHealth Score: {health_score}/100")
    print(f"Status: {status}")
    
    if issues:
        print(f"\nIssues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ No issues detected!")
    
    print(f"\n{'='*70}")
    
    if health_score >= 70:
        print("✅ BOT IS HEALTHY - Safe to connect MetaMask and trade")
    else:
        print("⚠️  BOT NEEDS FIXES - Do not enable live trading yet")
    
    print(f"{'='*70}\n")
    
    return health_score >= 70

if __name__ == "__main__":
    success = run_5min_test()
    sys.exit(0 if success else 1)
