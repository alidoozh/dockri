import requests
import pandas as pd
from datetime import datetime, timezone

BINANCE_DOMAINS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api3.binance.com"
]

def get_spot_price():
    last_error = None
    for base in BINANCE_DOMAINS:
        try:
            url = f"{base}/api/v3/ticker/price?symbol=BTCUSDT"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return float(r.json()['price'])
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"Failed to fetch spot price from all Binance domains: {last_error}")

def get_recent_minutes(limit=240):
    last_error = None
    for base in BINANCE_DOMAINS:
        try:
            url = f"{base}/api/v3/klines"
            params = {"symbol":"BTCUSDT","interval":"1m","limit":limit}
            r = requests.get(url, params=params, timeout=10)
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
            last_error = e
            continue
    raise RuntimeError(f"Failed to fetch OHLCV from all Binance domains: {last_error}")
