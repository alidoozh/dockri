def regime_score(macd_hist: float, rsi: float) -> float:
    s=0.0
    if macd_hist>0: s+=0.5
    if rsi>55: s+=0.5
    if macd_hist<0: s-=0.5
    if rsi<45: s-=0.5
    return max(-1.0, min(1.0, s))
