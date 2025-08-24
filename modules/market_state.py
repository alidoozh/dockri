def market_state_score(ema_fast: float, ema_slow: float) -> float:
    dist=(ema_fast/ema_slow)-1.0
    return max(-1.0, min(1.0, dist/0.01))
