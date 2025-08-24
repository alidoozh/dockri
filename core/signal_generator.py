def trade_plan(price: float, rr: float, atr_pct: float):
    stop = max(price*max(atr_pct,0.0015), price*0.0015)
    sl = price - stop
    tp = price + stop*rr
    return sl, tp

def label_from_conf(conf: float) -> str:
    if conf>=0.7: return "BUY"
    if conf<=0.3: return "SELL"
    return "HOLD"
