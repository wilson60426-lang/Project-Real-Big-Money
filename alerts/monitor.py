import argparse
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from data.providers import get_asset
from alerts.engine import evaluate_price_alert
from alerts.notifiers import send_telegram

load_dotenv()
CONFIG=Path("alerts/alerts.json")
STATE=Path("alerts/state.json")

def load_json(path,default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def check_once():
    rules=load_json(CONFIG,[])
    state=load_json(STATE,{})
    if not rules:
        print("尚未設定提醒。請先在 alerts/alerts.json 建立規則。")
        return
    for rule in rules:
        if not rule.get("enabled",True):
            continue
        asset=rule["asset"]
        target=float(rule["target"])
        direction=rule.get("direction","below")
        d=get_asset(asset,"Crypto",1,"1h")
        if d.empty:
            print(asset+" 資料取得失敗")
            continue
        price=float(d["close"].iloc[-1])
        result=evaluate_price_alert(price,target,direction)
        key=asset+":"+str(target)+":"+direction
        was=bool(state.get(key,False))
        print(asset+" $"+format(price,",.2f")+" -> "+result.status)
        if result.triggered and not was:
            arrow="≤" if direction=="below" else "≥"
            msg="🔔 Project Real Big Money\n"+asset+" 進入觀察區\n目前：$"+format(price,",.2f")+"\n條件："+arrow+" $"+format(target,",.2f")+"\n\n這是條件觸發提醒，不代表保證買點。"
            ok,detail=send_telegram(msg)
            print(detail)
        state[key]=result.triggered
    save_json(STATE,state)

def main():
    ap=argparse.ArgumentParser(description="Project Real Big Money 價格提醒監控器")
    ap.add_argument("--once",action="store_true",help="只檢查一次")
    ap.add_argument("--interval",type=int,default=300,help="檢查間隔秒數，預設 300")
    args=ap.parse_args()
    if args.once:
        check_once()
        return
    print("價格監控已啟動，每 "+str(args.interval)+" 秒檢查一次。Ctrl+C 可停止。")
    while True:
        check_once()
        time.sleep(max(30,args.interval))

if __name__=="__main__":
    main()
