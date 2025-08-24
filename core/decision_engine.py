import json, os

class DecisionEngine:
    def __init__(self, path='models/weights.json'):
        self.path=path
        self.weights={
            "mlp":0.22,"drl":0.22,"rsi":0.10,"macd":0.10,"volume":0.06,
            "whale_activity":0.10,"market_state":0.15,"sentiment":0.03,"regime":0.02,"atr":0.10
        }
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path,'r') as f:
                    self.weights.update(json.load(f))
        except Exception:
            pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path,'w') as f: json.dump(self.weights,f)

    def score(self, modules: dict) -> float:
        s=0.0; total_w=0.0
        for k,v in modules.items():
            w=self.weights.get(k,0.0); total_w+=w; s+=w*float(v)
        if total_w<=0: return 0.5
        conf = (s/total_w + 1.0)/2.0
        return max(0.0, min(1.0, conf))

    def update_bayesian(self, modules: dict, win: bool):
        lr = 0.03 if win else -0.03
        for k,v in modules.items():
            self.weights[k] = float(max(0.0, min(1.0, self.weights.get(k,0.0) + lr*abs(float(v)))))
        self.save()

    def auto_rr(self, atr_pct: float) -> float:
        if atr_pct<=0: return 2.0
        return max(1.5, min(6.0, 0.02/atr_pct))
