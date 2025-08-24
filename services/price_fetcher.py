import os, requests, pandas as pd
from datetime import datetime, timezone

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_MARKET = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

def get_spot_price():
    provider = os.getenv("PRICE_PROVIDER","coingecko").lower()
    if provider == "coingecko":
        try:
            r = requests.get(COINGECKO_SIMPLE, params={"ids":"bitcoin","vs_currencies":"usd"}, timeout=10)
            r.raise_for_status()
            return float(r.json()["bitcoin"]["usd"])
        except Exception:
            pass
    # fallback: Binance
    r = requests.get(BINANCE_TICKER, timeout=10)
    r.raise_for_status()
    return float(r.json()['price'])

def get_recent_minutes(limit=240):
    # Prefer Binance klines for OHLCV
    try:
        params = {"symbol":"BTCUSDT","interval":"1m","limit":limit}
        r = requests.get(BINANCE_KLINES, params=params, timeout=10)
        r.raise_for_status()
        data=[]
        for k in r.json():
            t=k[0]; h=float(k[2]); l=float(k[3]); c=float(k[4]); v=float(k[5])
            data.append({"time":datetime.fromtimestamp(t/1000,tz=timezone.utc), "price":c, "high":h, "low":l, "volume":v})
        return pd.DataFrame(data)
    except Exception:
        # Fallback: CoinGecko market chart (close + volume)
        r = requests.get(COINGECKO_MARKET, params={"vs_currency":"usd","days":"1","interval":"minute"}, timeout=10)
        r.raise_for_status()
        js=r.json()
        prices = js.get("prices", [])
        vols = js.get("total_volumes", [])
        # Align by timestamp index
        vol_map = {int(v[0]): float(v[1]) for v in vols}
        rows=[]
        for p in prices[-limit:]:
            ts=int(p[0]); c=float(p[1]); v=float(vol_map.get(ts, 0.0))
            rows.append({"time":datetime.fromtimestamp(ts/1000,tz=timezone.utc), "price":c, "high":c, "low":c, "volume":v})
        return pd.DataFrame(rows)
