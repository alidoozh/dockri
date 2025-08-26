import requests
import pandas as pd
from datetime import datetime, timezone

COINCAP_PRICE = "https://api.coincap.io/v2/assets/bitcoin"
COINGECKO_OHLC = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"

def get_spot_price():
    """قیمت لحظه‌ای BTC از CoinCap"""
    try:
        r = requests.get(COINCAP_PRICE, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data['data']['priceUsd'])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch spot price from CoinCap: {e}")


def get_recent_minutes(limit=240):
    """OHLCV دقیقه‌ای BTC از CoinGecko"""
    try:
        r = requests.get(COINGECKO_OHLC, params={
            "vs_currency": "usd",
            "days": "1"   # داده‌ی 1 روز اخیر
        }, timeout=10)
        r.raise_for_status()
        js = r.json()

        data = []
        for k in js[-limit:]:
            t = int(k[0]) / 1000
            o, h, l, c = k[1], k[2], k[3], k[4]
            data.append({
                "time": datetime.fromtimestamp(t, tz=timezone.utc),
                "open": o, "high": h, "low": l, "close": c, "volume": 0
            })
        return pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OHLCV from CoinGecko: {e}")
