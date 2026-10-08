import numpy as np
import pandas as pd
from backtesting.analytics import analyze
from backtesting.trade_engine import build_trades, trade_statistics

def classify_regimes(df):
    d=df.copy()
    d["ma200"]=d["close"].rolling(200).mean()
    d["ma50"]=d["close"].rolling(50).mean()
    d["vol"]=d["close"].pct_change().rolling(50).std()
    d["regime"]=np.where((d["close"]>d["ma200"])&(d["ma50"]>d["ma200"]),"牛市",
                 np.where((d["close"]<d["ma200"])&(d["ma50"]<d["ma200"]),"熊市","盤整"))
    return d

def regime_report(df, fee, timeframe):
    # Calculate returns on the full uninterrupted timeline BEFORE filtering regimes.
    d=classify_regimes(df)
    full,_=analyze(d,fee,timeframe)
    full["regime"]=d.loc[full.index,"regime"]
    out=[]
    for name in ["牛市","熊市","盤整"]:
        x=full.loc[full["regime"]==name,"strategy_return"]
        if len(x)<50: continue
        equity=(1+x).cumprod()
        peak=equity.cummax().clip(lower=1)
        drawdown=(equity/peak-1).min()
        std=x.std()
        ann={"1h":8760,"4h":2190,"1d":365}.get(timeframe,365)
        sharpe=float(np.sqrt(ann)*x.mean()/std) if pd.notna(std) and std>0 else 0.0
        out.append({"市場":name,"K線數":len(x),"報酬":float(equity.iloc[-1]-1),"最大回撤":float(drawdown),"Sharpe":sharpe})
    return pd.DataFrame(out)


def walk_forward(df, fee, timeframe, windows=5):
    n=len(df); step=max(100,n//(windows+2)); out=[]
    for i in range(windows):
        train_end=step*(i+2); test_end=min(train_end+step,n)
        if test_end<=train_end: break
        train=df.iloc[:train_end]; test=df.iloc[train_end:test_end]
        _,tm=analyze(train,fee,timeframe); _,vm=analyze(test,fee,timeframe)
        out.append({"區段":i+1,"開發期報酬":tm["total_return"],"驗證期報酬":vm["total_return"],
                    "驗證Sharpe":vm["sharpe"],"PASS":vm["total_return"]>0 and vm["sharpe"]>0})
    return pd.DataFrame(out)

def cost_stress(df, fee, timeframe, slippage):
    rows=[]
    for mult in [1,1.5,2,3]:
        f=fee*mult; s=slippage*mult
        trades=build_trades(df,f,s); st=trade_statistics(trades)
        rows.append({"成本情境":f"{mult:.1f}x","手續費":f,"滑價":s,"交易數":st["trades"],
                     "Expectancy":st["expectancy"],"Profit Factor":st["profit_factor"]})
    return pd.DataFrame(rows)

def validation_score(history_years, trade_stats, wf, regimes, stress):
    score=0; reasons=[]
    if history_years>=5: score+=20
    elif history_years>=3: score+=16
    elif history_years>=1: score+=10
    else: reasons.append("歷史跨度偏短")
    n=trade_stats["trades"]
    if n>=300: score+=20
    elif n>=100: score+=15
    elif n>=30: score+=8
    else: reasons.append("完整交易樣本不足")
    if len(wf):
        rate=float(wf["PASS"].mean())
        score+=round(25*rate)
        if rate<.6: reasons.append("Walk-Forward 通過率偏低")
    if len(regimes)>=3:
        positive=int((regimes["報酬"]>0).sum()); score+=positive*5
        if positive<2: reasons.append("跨市場環境適應性偏弱")
    if len(stress):
        last=stress.iloc[-1]
        if last["Expectancy"]>0: score+=20
        elif stress.iloc[0]["Expectancy"]>0: score+=10; reasons.append("交易成本提高後優勢消失")
        else: reasons.append("基礎交易期望值非正")
    score=min(100,int(score))
    status="PASS" if score>=80 else "WATCH" if score>=60 else "FAIL"
    return score,status,reasons
