import requests
import pandas as pd
from datetime import datetime, timezone

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

def get_spot_price():
    try:
        r = requests.get(BINANCE_TICKER, timeout=10)
        r.raise_for_status()
        return float(r.json()['price'])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch spot price from Binance: {e}")

def get_recent_minutes(limit=240):
    try:
        params = {"symbol":"BTCUSDT","interval":"1m","limit":limit}
        r = requests.get(BINANCE_KLINES, params=params, timeout=10)
        r.raise_for_status()
        data = []
        for k in r.json():
            t = k[0]
            h = float(k[2])
            l = float(k[3])
            c = float(k[4])
            v = float(k[5])
            data.append({
                "time": datetime.fromtimestamp(t/1000, tz=timezone.utc),
                "price": c,
                "high": h,
                "low": l,
                "volume": v
            })
        return pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OHLCV from Binance: {e}")
