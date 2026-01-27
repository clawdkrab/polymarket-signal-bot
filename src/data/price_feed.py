#!/usr/bin/env python3
"""
BTC Price Feed
Fetches historical BTC prices for technical analysis.
"""
import requests
from typing import List
from datetime import datetime, timedelta


class BTCPriceFeed:
    """Fetch BTC price data for analysis."""
    
    def __init__(self):
        # Use CoinCap (free, no auth required)
        self.coincap_url = "https://api.coincap.io/v2"
    
    def get_recent_prices(self, minutes: int = 300) -> List[float]:
        """
        Get recent BTC prices.
        
        Args:
            minutes: Number of minutes of history (default 300 = 5 hours)
        
        Returns:
            List of prices (oldest first)
        """
        try:
            # CoinCap provides hourly data for free
            endpoint = f"{self.coincap_url}/assets/bitcoin/history"
            params = {
                "interval": "h1",  # 1-hour intervals
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = [float(item["priceUsd"]) for item in data.get("data", [])]
            
            # Return last N hours
            hours_needed = max(1, minutes // 60)
            return prices[-hours_needed:] if prices else []
        
        except Exception as e:
            print(f"⚠️  Error fetching BTC prices from CoinCap: {e}")
            # Try backup source
            return self._get_backup_prices()
    
    def _get_backup_prices(self) -> List[float]:
        """Backup price source using Binance public API."""
        try:
            endpoint = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": "BTCUSDT",
                "interval": "1h",
                "limit": 24  # Last 24 hours
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Kline format: [timestamp, open, high, low, close, ...]
            prices = [float(candle[4]) for candle in data]  # Close prices
            
            return prices
        
        except Exception as e:
            print(f"⚠️  Backup price source also failed: {e}")
            return []
    
    def get_current_price(self) -> float:
        """Get current BTC price."""
        try:
            endpoint = f"{self.coincap_url}/assets/bitcoin"
            
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return float(data.get("data", {}).get("priceUsd", 0.0))
        
        except Exception as e:
            # Try Binance backup
            try:
                endpoint = "https://api.binance.com/api/v3/ticker/price"
                params = {"symbol": "BTCUSDT"}
                
                response = requests.get(endpoint, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                return float(data.get("price", 0.0))
            
            except Exception as e2:
                print(f"⚠️  Error fetching current BTC price: {e}")
                print(f"⚠️  Backup source also failed: {e2}")
                return 0.0
    
    def estimate_15min_prices(self, hourly_prices: List[float]) -> List[float]:
        """
        Estimate 15-min prices from hourly data using linear interpolation.
        
        This is a fallback since free APIs don't offer 15-min candles.
        In production, consider upgrading to a paid API.
        """
        if len(hourly_prices) < 2:
            return hourly_prices
        
        estimated = []
        
        for i in range(len(hourly_prices) - 1):
            start_price = hourly_prices[i]
            end_price = hourly_prices[i + 1]
            
            # Generate 4 intermediate points (15-min intervals in 1 hour)
            for j in range(4):
                interpolated = start_price + (end_price - start_price) * (j / 4)
                estimated.append(interpolated)
        
        # Add final price
        estimated.append(hourly_prices[-1])
        
        return estimated
