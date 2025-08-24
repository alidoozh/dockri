# Proxy using volume anomaly: positive z = potential accumulation (whales)
def whale_score(vol_z: float) -> float:
    return max(-1.0, min(1.0, vol_z/3.0))
