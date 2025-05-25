#!/usr/bin/env python3
"""
Simple script to test the Paper Trading API endpoints.
Run this after starting the API server with `python run_api.py`.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def print_response(response, endpoint):
    """Print formatted API response"""
    print(f"\n=== {endpoint} ===")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    else:
        print(f"Error: {response.text}")
    print("=" * 50)

def test_api():
    """Test various API endpoints"""
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Root Endpoint")
    
    # Test account endpoints
    response = requests.get(f"{BASE_URL}/account/balance")
    print_response(response, "Account Balance")
    
    response = requests.get(f"{BASE_URL}/account/usdt-balance")
    print_response(response, "USDT Balance")
    
    response = requests.get(f"{BASE_URL}/account/portfolio")
    print_response(response, "Portfolio")
    
    # Test market endpoints
    response = requests.get(f"{BASE_URL}/market/pairs")
    print_response(response, "Currency Pairs")
    
    response = requests.get(f"{BASE_URL}/market/price/BTC%2FUSDT")
    print_response(response, "BTC/USDT Price")
    
    # Test order endpoints
    response = requests.get(f"{BASE_URL}/orders/fulfilled")
    print_response(response, "Fulfilled Orders")
    
    response = requests.get(f"{BASE_URL}/orders/open")
    print_response(response, "Open Orders")
    
    # Test PnL calculation
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    
    time_range = {
        "start_time": one_year_ago.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    response = requests.post(
        f"{BASE_URL}/trades/pnl/calculate", 
        json=time_range
    )
    print_response(response, "PnL Calculation")

if __name__ == "__main__":
    print("Testing Paper Trading API...")
    test_api()
    print("\nAPI testing completed!")