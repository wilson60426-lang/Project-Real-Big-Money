import numpy as np
import pandas as pd
from backtesting.analytics import analyze
from backtesting.trade_engine import build_trades, trade_statistics
from backtesting.validation import regime_report, walk_forward, cost_stress

def bootstrap_expectancy(trades, n=1000, seed=42):
    if trades.empty: return {"median":0,"p05":0,"p95":0,"positive_probability":0}
    rng=np.random.default_rng(seed); r=trades["淨報酬"].to_numpy()
    means=np.array([rng.choice(r,size=len(r),replace=True).mean() for _ in range(n)])
    return {"median":float(np.median(means)),"p05":float(np.quantile(means,.05)),"p95":float(np.quantile(means,.95)),"positive_probability":float((means>0).mean())}

def monte_carlo_drawdown(trades,n=1000,seed=42):
    if trades.empty:return {"median_max_dd":0,"p95_worst_dd":0}
    rng=np.random.default_rng(seed); r=trades["淨報酬"].to_numpy(); dds=[]
    for _ in range(n):
        x=rng.choice(r,size=len(r),replace=True); eq=np.cumprod(1+x); peak=np.maximum.accumulate(eq); dds.append(float((eq/peak-1).min()))
    return {"median_max_dd":float(np.median(dds)),"p95_worst_dd":float(np.quantile(dds,.05))}

def yearly_test(df,fee,timeframe):
    d=df.copy(); d["year"]=pd.to_datetime(d["timestamp"]).dt.year; rows=[]
    for year,x in d.groupby("year"):
        if len(x)<50: continue
        _,m=analyze(x,fee,timeframe)
        rows.append({"年份":int(year),"報酬":m["total_return"],"Sharpe":m["sharpe"],"最大回撤":m["max_drawdown"],"PASS":m["total_return"]>0})
    return pd.DataFrame(rows)

def challenge_strategy(df,fee,timeframe,slippage):
    trades=build_trades(df,fee,slippage); ts=trade_statistics(trades)
    boot=bootstrap_expectancy(trades); mc=monte_carlo_drawdown(trades); yearly=yearly_test(df,fee,timeframe)
    regimes=regime_report(df,fee,timeframe); wf=walk_forward(df,fee,timeframe,5); stress=cost_stress(df,fee,timeframe,slippage)
    checks=[]
    def add(name,ok,watch,detail): checks.append({"挑戰":name,"結果":"PASS" if ok else "WATCH" if watch else "FAIL","說明":detail})
    add("交易樣本",ts["trades"]>=100,ts["trades"]>=30,f"{ts['trades']} 筆完整交易")
    add("Bootstrap 期望值",boot["p05"]>0,boot["positive_probability"]>=.7,f"正期望重抽樣比例 {boot['positive_probability']:.1%}")
    yrpass=float(yearly["PASS"].mean()) if len(yearly) else 0
    add("跨年份",yrpass>=.7,yrpass>=.5,f"{int(yearly['PASS'].sum()) if len(yearly) else 0}/{len(yearly)} 年為正")
    regpass=int((regimes["報酬"]>0).sum()) if len(regimes) else 0
    add("牛熊盤整",regpass>=2,regpass>=1,f"{regpass}/{len(regimes)} 種環境為正")
    wfr=float(wf["PASS"].mean()) if len(wf) else 0
    add("Walk-Forward",wfr>=.6,wfr>=.4,f"{int(wf['PASS'].sum()) if len(wf) else 0}/{len(wf)} 區段通過")
    hard=stress.iloc[-1] if len(stress) else None
    hard_ok=hard is not None and hard["Expectancy"]>0
    base_ok=len(stress)>0 and stress.iloc[0]["Expectancy"]>0
    add("3倍成本壓力",hard_ok,base_ok,"3倍成本後仍有正期望" if hard_ok else "成本提高後優勢減弱或消失")
    passed=sum(x["結果"]=="PASS" for x in checks); watched=sum(x["結果"]=="WATCH" for x in checks)
    score=round((passed+.5*watched)/len(checks)*100) if checks else 0
    status="PASS" if score>=80 else "WATCH" if score>=60 else "FAIL"
    return {"score":score,"status":status,"checks":pd.DataFrame(checks),"trade_stats":ts,"bootstrap":boot,"monte_carlo":mc,"yearly":yearly,"regimes":regimes,"walk_forward":wf,"stress":stress}
