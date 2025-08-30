import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone

# تنظیمات (از ENV می‌خواند ولی پیش‌فرض دارد)
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "10"))  # برای spot
OHLCV_INTERVAL = int(os.getenv("OHLCV_INTERVAL", "60"))  # برای کندل‌ها (ثانیه)

COINCAP_PRICE = "https://api.coincap.io/v2/assets/bitcoin"
COINGECKO_OHLC = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"

def get_spot_price():
    """قیمت لحظه‌ای BTC از CoinCap (spot)"""
    try:
        r = requests.get(COINCAP_PRICE, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data['data']['priceUsd'])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch spot price from CoinCap: {e}")

def get_recent_minutes_from_coingecko(limit=240):
    """
    OHLC از CoinGecko (coingecko ohlc returns 1, 14, 30 days based buckets).
    We'll request days=1 and slice last `limit` entries.
    """
    try:
        r = requests.get(COINGECKO_OHLC, params={
            "vs_currency": "usd",
            "days": "1"
        }, timeout=15)
        r.raise_for_status()
        js = r.json()
        data = []
        # js is list of [timestamp, open, high, low, close]
        for k in js[-limit:]:
            t = int(k[0]) / 1000.0
            o, h, l, c = k[1], k[2], k[3], k[4]
            data.append({
                "time": datetime.fromtimestamp(t, tz=timezone.utc),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": 0.0
            })
        return pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OHLCV from CoinGecko: {e}")

# public helper used by main.py
def get_recent_minutes(limit=240, last_ohlcv_ts_holder: dict = None):
    """
    Public function to get OHLCV.
    - If last_ohlcv_ts_holder is provided (dict), caller can control rate (timestamp).
    - This function delegates to CoinGecko (reliable for OHLC).
    """
    # direct call to coingecko - caller controls frequency
    return get_recent_minutes_from_coingecko(limit=limit)
