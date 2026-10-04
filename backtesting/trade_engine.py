import pandas as pd
import numpy as np

def build_trades(df: pd.DataFrame, fee_rate: float = 0.001, slippage: float = 0.0005) -> pd.DataFrame:
    d=df.dropna(subset=["close","signal"]).copy().reset_index(drop=True)
    d["exec_position"]=d["signal"].shift(1).fillna(0).astype(int)
    trades=[]
    current=None

    for i,row in d.iterrows():
        pos=int(row["exec_position"])
        price=float(row["close"])
        ts=row["timestamp"]

        if current is None and pos != 0:
            current={"side":pos,"entry_i":i,"entry_time":ts,"entry_price":price}

        elif current is not None and pos != current["side"]:
            exit_i=i
            segment=d.iloc[current["entry_i"]:exit_i+1]
            side=current["side"]
            entry=current["entry_price"]
            exit_price=price
            gross=(exit_price/entry-1)*side
            costs=2*(fee_rate+slippage)
            net=gross-costs
            path=((segment["close"]/entry)-1)*side
            mae=float(path.min()) if len(path) else 0.0
            mfe=float(path.max()) if len(path) else 0.0
            bars=max(1,exit_i-current["entry_i"])
            trades.append({
                "進場時間":current["entry_time"],"出場時間":ts,
                "方向":"做多" if side==1 else "做空",
                "進場價":entry,"出場價":exit_price,
                "毛報酬":gross,"交易成本":costs,"淨報酬":net,
                "MAE":mae,"MFE":mfe,"持有K線數":bars
            })
            current=None
            if pos != 0:
                current={"side":pos,"entry_i":i,"entry_time":ts,"entry_price":price}

    return pd.DataFrame(trades)

def trade_statistics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"trades":0,"win_rate":0.0,"avg_win":0.0,"avg_loss":0.0,"payoff":0.0,
                "expectancy":0.0,"profit_factor":0.0,"max_consecutive_losses":0,
                "avg_holding_bars":0.0,"avg_mae":0.0,"avg_mfe":0.0}
    r=trades["淨報酬"]
    wins=r[r>0]; losses=r[r<0]
    avg_win=float(wins.mean()) if len(wins) else 0.0
    avg_loss=float(losses.mean()) if len(losses) else 0.0
    win_rate=float((r>0).mean())
    payoff=avg_win/abs(avg_loss) if avg_loss<0 else float("inf") if avg_win>0 else 0.0
    pf=float(wins.sum()/abs(losses.sum())) if len(losses) and losses.sum()!=0 else float("inf") if len(wins) else 0.0
    expectancy=float(r.mean())
    streak=max_streak=0
    for x in r:
        if x<0:
            streak+=1; max_streak=max(max_streak,streak)
        else: streak=0
    return {
        "trades":int(len(trades)),"win_rate":win_rate,"avg_win":avg_win,"avg_loss":avg_loss,
        "payoff":payoff,"expectancy":expectancy,"profit_factor":pf,
        "max_consecutive_losses":int(max_streak),
        "avg_holding_bars":float(trades["持有K線數"].mean()),
        "avg_mae":float(trades["MAE"].mean()),"avg_mfe":float(trades["MFE"].mean())
    }
