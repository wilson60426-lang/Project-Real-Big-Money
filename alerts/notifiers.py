import os
import json
import urllib.parse
import urllib.request

def telegram_configured():
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))

def send_telegram(message: str):
    token=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
    chat_id=os.getenv("TELEGRAM_CHAT_ID","").strip()
    if not token or not chat_id:
        return False,"尚未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID"
    url="https://api.telegram.org/bot"+token+"/sendMessage"
    data=urllib.parse.urlencode({"chat_id":chat_id,"text":message}).encode()
    try:
        req=urllib.request.Request(url,data=data,method="POST")
        with urllib.request.urlopen(req,timeout=15) as r:
            payload=json.loads(r.read().decode("utf-8"))
        return bool(payload.get("ok")), "Telegram 已送出" if payload.get("ok") else str(payload)
    except Exception as e:
        return False,"Telegram 發送失敗："+str(e)
