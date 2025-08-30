import os, threading, time
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import ta, pandas as pd

from services.price_fetcher import get_spot_price, get_recent_minutes
from modules.rsi_divergence import rsi_and_divergence
from modules.macd import macd_features
from modules.volume import volume_features
from modules.whale_activity import whale_score
from modules.market_state import market_state_score
from modules.sentiment import sentiment_score
from modules.regime_filter import regime_score

from core.decision_engine import DecisionEngine
from core.feedback_loop import apply_feedback
from core.signal_generator import trade_plan, label_from_conf
from core.trade_logger import log_open, recent
from services.telegram_sender import send_text

# === تنظیمات محیطی ===
POLL_INTERVAL = float(os.getenv('POLL_INTERVAL', '10'))  # spot poll (s)
OHLCV_FETCH_INTERVAL = int(os.getenv('OHLCV_FETCH_INTERVAL', '60'))  # ohlcv poll (s)
MIN_OHLCV_ROWS = int(os.getenv('MIN_OHLCV_ROWS', '30'))  # حداقل کندل برای تحلیل

MANUAL_RR = os.getenv('MANUAL_RR', '')
MANUAL_RR = float(MANUAL_RR) if MANUAL_RR.strip() else None

# === FastAPI ===
app = FastAPI()
templates = Jinja2Templates(directory="ui/templates")

state = {
    "price": None, "updated_at": None, "decision": None, "entry": None,
    "sl": None, "tp": None, "rr": None, "confidence": 0.0, "modules": {}
}
de = DecisionEngine()
open_position = None
_test_sent = False

# === اندیکاتورها ===
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    # اطمینان از ستون close موجود است
    if 'close' not in x.columns and 'price' in x.columns:
        x['close'] = x['price']
    ema20 = ta.trend.EMAIndicator(x['close'], window=20).ema_indicator()
    ema50 = ta.trend.EMAIndicator(x['close'], window=50).ema_indicator()
    macd = ta.trend.MACD(x['close'])
    x['ema20'] = ema20; x['ema50'] = ema50
    x['macd'] = macd.macd(); x['macd_signal'] = macd.macd_signal(); x['macd_hist'] = macd.macd_diff()
    rsi = ta.momentum.RSIIndicator(x['close'], window=14).rsi()
    tr1 = (x['high'] - x['low']).abs()
    tr2 = (x['high'] - x['close'].shift()).abs()
    tr3 = (x['low'] - x['close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    x['atr_pct'] = (tr.rolling(14).mean() / x['close']).clip(lower=0)
    x['rsi'] = rsi
    x['volume'] = x.get('volume', pd.Series()).fillna(0)
    x.dropna(inplace=True)
    return x

# === موتور سیگنال ===
def engine_loop():
    global state, de, open_position, _test_sent
    last_ohlcv_fetch_ts = 0
    df_cache = None

    while True:
        try:
            if not _test_sent:
                try:
                    send_text("✅ AlidoozhEngine Pro started. Test message.")
                except Exception:
                    pass
                _test_sent = True

            # --- spot price (CoinCap) ---
            try:
                spot_price = get_spot_price()
            except Exception as e:
                print("engine loop error: spot fetch failed:", e)
                # اگر spot نیامد صبر کن و دوباره امتحان کن
                time.sleep(POLL_INTERVAL)
                continue

            # --- OHLCV فقط در فواصل OHLCV_FETCH_INTERVAL ---
            now = time.time()
            if (df_cache is None) or (now - last_ohlcv_fetch_ts >= OHLCV_FETCH_INTERVAL):
                try:
                    df_new = get_recent_minutes(limit=240)
                    if df_new is None or df_new.empty or len(df_new) < MIN_OHLCV_ROWS:
                        # اگر داده کافی نیست، فقط کش را بروزرسانی نکن، و از کش قبلی استفاده می‌کنیم
                        print("engine loop warning: OHLCV insufficient or empty, skipping update.")
                    else:
                        df_cache = df_new
                        last_ohlcv_fetch_ts = now
                except Exception as e:
                    print("engine loop error: Failed to fetch OHLCV:", e)
                    # در صورت خطا از کش استفاده کن (اگر موجود نیست، منتظر بمان)
                    if df_cache is None or df_cache.empty:
                        time.sleep(POLL_INTERVAL)
                        continue

            # اگر کش خالی است، نمی‌توانیم اندیکاتور بسازیم — فقط قیمت را آپدیت می‌کنیم و به حلقه ادامه می‌دهیم
            if df_cache is None or df_cache.empty or len(df_cache) < MIN_OHLCV_ROWS:
                # بروز رسانی وضعیت با spot و گذر
                state.update({
                    "price": spot_price,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "decision": None,
                    "entry": None,
                    "sl": None,
                    "tp": None,
                    "rr": None,
                    "confidence": 0.0,
                    "modules": {}
                })
                time.sleep(POLL_INTERVAL)
                continue

            # --- تحلیل کامل با کندل‌ها ---
            ind = compute_indicators(df_cache)
            if ind.empty:
                print("engine loop warning: computed indicators empty, skipping.")
                time.sleep(POLL_INTERVAL)
                continue

            last = ind.iloc[-1]
            price = float(last['close'])  # استفاده از کندل برای consistency

            rsi_df = rsi_and_divergence(ind)
            macd_df = macd_features(ind)
            vol_df = volume_features(ind)

            rsi = float(rsi_df['rsi'].iloc[-1])
            macd_delta = float(macd_df['macd'].iloc[-1] - macd_df['macd_signal'].iloc[-1])
            macd_hist = float(macd_df['macd_hist'].iloc[-1])
            ema20 = float(last['ema20']); ema50 = float(last['ema50'])
            atr_pct = float(last['atr_pct'])
            vol_z = float(vol_df['vol_z'].iloc[-1])

            mods = {}
            mods['rsi'] = (rsi - 50) / 50
            mods['macd'] = max(-1.0, min(1.0, macd_delta / (price * 0.001 + 1e-9)))
            mods['volume'] = max(-1.0, min(1.0, vol_z / 3.0))
            mods['whale_activity'] = whale_score(vol_z)
            mods['market_state'] = market_state_score(ema20, ema50)
            mods['sentiment'] = sentiment_score()
            mods['regime'] = regime_score(macd_hist, rsi)
            mods['atr'] = max(-1.0, min(1.0, (0.02 - atr_pct) / 0.02))
            mods['mlp'] = 0.0
            mods['drl'] = 0.0

            conf = de.score(mods)
            rr = MANUAL_RR if MANUAL_RR is not None else de.auto_rr(atr_pct)
            decision = label_from_conf(conf)
            sl, tp = trade_plan(price, rr, atr_pct)

            state.update({
                "price": price,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "decision": decision,
                "entry": price,
                "sl": sl,
                "tp": tp,
                "rr": rr,
                "confidence": conf,
                "modules": mods
            })

            # ارسال سیگنال در صورت برآورده شدن شرط
            if decision == "BUY" and conf >= 0.7 and open_position is None:
                log_open("LONG", price, sl, tp, rr, conf, mods)
                try:
                    send_text(f"🚀 BTC Signal\nEntry: ${price:.2f}\nSL: ${sl:.2f}\nTP: ${tp:.2f}\nRR: {rr:.2f}\nConf: {conf*100:.0f}%")
                except Exception:
                    pass
                open_position = {"side": "LONG", "entry": price, "sl": sl, "tp": tp, "mods": mods}

            # مدیریت پوزیشن باز
            if open_position:
                if price >= open_position['tp']:
                    apply_feedback(de, open_position['mods'], hit_tp=True, hit_sl=False)
                    try:
                        send_text(f"✅ TP hit: +{(open_position['tp']-open_position['entry'])/open_position['entry']*100:.2f}%")
                    except Exception:
                        pass
                    open_position = None
                elif price <= open_position['sl']:
                    apply_feedback(de, open_position['mods'], hit_tp=False, hit_sl=True)
                    try:
                        send_text(f"❌ SL hit: {(open_position['sl']-open_position['entry'])/open_position['entry']*100:.2f}%")
                    except Exception:
                        pass
                    open_position = None

        except Exception as e:
            print("engine loop error:", e)

        time.sleep(POLL_INTERVAL)


# === رویداد استارتاپ ===
@app.on_event("startup")
def startup():
    threading.Thread(target=engine_loop, daemon=True).start()


# === API ها ===
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/signal")
def api_signal():
    return state

@app.get("/api/weights")
def api_weights():
    from core.decision_engine import DecisionEngine
    return {"weights": DecisionEngine().weights}

@app.get("/api/trades")
def api_trades(limit: int = Query(30, ge=1, le=200)):
    from core.trade_logger import recent
    return {"trades": recent(limit)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT","8000")))
