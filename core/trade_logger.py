import csv, os, json
from datetime import datetime, timezone

LOG="logs/trades.csv"
os.makedirs("logs", exist_ok=True)
if not os.path.exists(LOG):
    with open(LOG,'w',newline='',encoding='utf-8') as f:
        csv.writer(f).writerow(["time","side","entry","sl","tp","rr","confidence","status","exit_price","pnl_pct","modules"])

def log_open(side, entry, sl, tp, rr, confidence, modules_dict):
    with open(LOG,'a',newline='',encoding='utf-8') as f:
        csv.writer(f).writerow([datetime.now(timezone.utc).isoformat(), side, entry, sl, tp, rr, confidence, "OPEN", "", "", json.dumps(modules_dict)])

def recent(limit=50):
    import pandas as pd
    if not os.path.exists(LOG): return []
    df=pd.read_csv(LOG)
    return df.tail(limit).to_dict(orient='records')
