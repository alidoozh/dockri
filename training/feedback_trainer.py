import os, json, pandas as pd
from core.decision_engine import DecisionEngine

def run():
    if not os.path.exists("logs/trades.csv"): 
        print("no trades"); return
    df=pd.read_csv("logs/trades.csv")
    if df.empty: return
    de=DecisionEngine()
    for _,row in df.iterrows():
        try:
            modules=json.loads(row['modules'])
        except Exception:
            modules={}
        if str(row.get('status','OPEN')).upper()!="CLOSED": 
            continue
        pnl=float(row.get('pnl_pct',0) or 0)
        if pnl>0: de.update_bayesian(modules, True)
        elif pnl<0: de.update_bayesian(modules, False)
    print("weights updated:", de.weights)

if __name__=='__main__':
    run()
