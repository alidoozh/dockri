import os, requests
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN','')
CHAT_ID=os.getenv('TELEGRAM_CHAT_ID','')

def send_text(text: str):
    if not TOKEN or not CHAT_ID: return {"ok":False,"error":"missing token/chat id"}
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      json={"chat_id":CHAT_ID,"text":text}, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok":False,"error":str(e)}
