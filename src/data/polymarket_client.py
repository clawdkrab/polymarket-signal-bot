#!/usr/bin/env python3
"""
Polymarket CLOB Client
Custom REST API implementation for Polymarket trading.
"""
import requests
import hmac
import hashlib
import base64
import time
import json
from typing import Dict, List, Optional
from pathlib import Path


class PolymarketClient:
    """Lightweight Polymarket CLOB API client."""
    
    def __init__(self, credentials_path: str = None):
        self.clob_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        
        # Load API credentials
        if credentials_path is None:
            credentials_path = str(Path.home() / ".polymarket_credentials.json")
        
        with open(credentials_path) as f:
            creds = json.load(f)
            self.api_key = creds["api_key"]
            self.secret = creds["secret"]
            self.passphrase = creds["passphrase"]
    
    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate HMAC signature for L2 authentication."""
        timestamp = str(int(time.time()))
        
        # Create message to sign: timestamp + method + path + body
        message = timestamp + method + path + body
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # Base64 encode the signature
        signature_b64 = base64.b64encode(signature).decode()
        
        return {
            "POLY_API_KEY": self.api_key,
            "POLY_SIGNATURE": signature_b64,
            "POLY_TIMESTAMP": timestamp,
            "POLY_PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None, auth: bool = True) -> dict:
        """Make authenticated API request."""
        url = f"{self.clob_url}{endpoint}"
        body = json.dumps(data) if data else ""
        
        headers = {}
        if auth:
            headers = self._sign_request(method, endpoint, body)
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=body)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, data=body)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    # ===== PUBLIC ENDPOINTS =====
    
    def get_markets(self, limit: int = 100, next_cursor: str = None) -> List[dict]:
        """Get all markets from Gamma API."""
        params = {"limit": limit}
        if next_cursor:
            params["next_cursor"] = next_cursor
        
        url = f"{self.gamma_url}/markets"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def search_markets(self, query: str) -> List[dict]:
        """Search for markets by keyword."""
        markets = self.get_markets(limit=500)
        results = []
        
        query_lower = query.lower()
        for market in markets:
            if query_lower in market.get("question", "").lower():
                results.append(market)
        
        return results
    
    def get_orderbook(self, token_id: str) -> dict:
        """Get orderbook for a token."""
        endpoint = f"/book?token_id={token_id}"
        # Orderbook is public, no auth needed
        url = f"{self.clob_url}{endpoint}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_midpoint(self, token_id: str) -> float:
        """Get midpoint price for a token."""
        endpoint = f"/midpoint?token_id={token_id}"
        url = f"{self.clob_url}{endpoint}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data.get("mid", 0))
    
    # ===== AUTHENTICATED ENDPOINTS =====
    
    def get_balance(self) -> dict:
        """Get account balance."""
        return self._request("GET", "/balances")
    
    def get_open_orders(self) -> List[dict]:
        """Get all open orders."""
        return self._request("GET", "/orders")
    
    def place_order(
        self,
        token_id: str,
        side: str,  # "BUY" or "SELL"
        price: float,
        size: float,
        order_type: str = "GTC"  # GTC, FOK, IOC
    ) -> dict:
        """
        Place a limit order.
        
        Args:
            token_id: Market token ID
            side: BUY or SELL
            price: Price per share (0.00 to 1.00)
            size: Number of shares
            order_type: GTC (Good Till Cancel), FOK (Fill or Kill), IOC (Immediate or Cancel)
        """
        order_data = {
            "token_id": token_id,
            "side": side.upper(),
            "price": str(price),
            "size": str(size),
            "order_type": order_type
        }
        
        return self._request("POST", "/order", order_data)
    
    def cancel_order(self, order_id: str) -> dict:
        """Cancel a specific order."""
        return self._request("DELETE", f"/order/{order_id}")
    
    def cancel_all_orders(self) -> dict:
        """Cancel all open orders."""
        return self._request("DELETE", "/orders")
    
    def get_trades(self, limit: int = 100) -> List[dict]:
        """Get recent trades."""
        return self._request("GET", f"/trades?limit={limit}")
