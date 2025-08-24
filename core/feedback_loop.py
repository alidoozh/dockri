from .decision_engine import DecisionEngine

def apply_feedback(engine: DecisionEngine, modules: dict, hit_tp: bool, hit_sl: bool):
    if hit_tp and not hit_sl:
        engine.update_bayesian(modules, True)
    elif hit_sl and not hit_tp:
        engine.update_bayesian(modules, False)
