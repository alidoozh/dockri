import time
import requests
import pandas as pd
from datetime import datetime, timezone

# --- تنظیم ثابت ---
POLL_INTERVAL = 10  # هر 10 ثانیه یکبار

COINCAP_PRICE = "https://api.coincap.io/v2/assets/bitcoin"
COINCAP_HISTORY = "https://api.coincap.io/v2/candles"


def get_spot_price():
    """دریافت قیمت لحظه‌ای BTC از CoinCap"""
    try:
        r = requests.get(COINCAP_PRICE, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data['data']['priceUsd'])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch spot price from CoinCap: {e}")


def get_recent_minutes(limit=240):
    """دریافت OHLCV دقیقه‌ای BTC از CoinCap"""
    try:
        r = requests.get(COINCAP_HISTORY, params={
            "exchange": "binance",     # منبع داده
            "interval": "m1",          # کندل 1 دقیقه‌ای
            "baseId": "bitcoin",
            "quoteId": "tether",
            "limit": limit
        }, timeout=10)
        r.raise_for_status()
        js = r.json()
        data = []
        for k in js['data']:
            t = int(k['period'])
            o = float(k['open'])
            h = float(k['high'])
            l = float(k['low'])
            c = float(k['close'])
            v = float(k['volume'])
            data.append({
                "time": datetime.fromtimestamp(t / 1000, tz=timezone.utc),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v
            })
        return pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OHLCV from CoinCap: {e}")


# --- حالت تست مستقل ---
if __name__ == "__main__":
    while True:
        try:
            price = get_spot_price()
            print(f"[BTC/USDT] Spot Price: {price:.2f}")
            df = get_recent_minutes(limit=5)
            print(df.tail(1))
        except Exception as e:
            print("[ERROR]", e)
        time.sleep(POLL_INTERVAL)
