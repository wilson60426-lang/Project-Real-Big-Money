import numpy as np
import pandas as pd

PERIODS={"15m":365*24*4,"1h":365*24,"4h":365*6,"1d":365}

def analyze(df: pd.DataFrame, fee_rate: float, timeframe: str) -> tuple[pd.DataFrame,dict]:
    d=df.dropna(subset=["close","signal"]).copy()
    d["market_return"]=d["close"].pct_change().fillna(0)
    d["position"]=d["signal"].shift(1).fillna(0)
    d["turnover"]=d["position"].diff().abs().fillna(d["position"].abs())
    d["strategy_return"]=d["position"]*d["market_return"]-d["turnover"]*fee_rate
    d["strategy_equity"]=(1+d["strategy_return"]).cumprod()
    d["buy_hold_equity"]=(1+d["market_return"]).cumprod()
    peak=d["strategy_equity"].cummax()
    dd=d["strategy_equity"]/peak-1
    r=d["strategy_return"]
    ann=PERIODS.get(timeframe,365)
    std=r.std()
    sharpe=float(np.sqrt(ann)*r.mean()/std) if std and not np.isnan(std) else 0.0
    downside=r[r<0].std()
    sortino=float(np.sqrt(ann)*r.mean()/downside) if downside and not np.isnan(downside) else 0.0
    wins=r[r>0].sum(); losses=-r[r<0].sum()
    profit_factor=float(wins/losses) if losses>0 else float("inf")
    active=r[d["position"]!=0]
    win_rate=float((active>0).mean()) if len(active) else 0.0
    metrics={
      "total_return":float(d["strategy_equity"].iloc[-1]-1) if len(d) else 0.0,
      "buy_hold":float(d["buy_hold_equity"].iloc[-1]-1) if len(d) else 0.0,
      "max_drawdown":float(dd.min()) if len(dd) else 0.0,
      "sharpe":sharpe,"sortino":sortino,"profit_factor":profit_factor,
      "win_rate":win_rate,"position_changes":int((d["turnover"]>0).sum())
    }
    return d,metrics

def split_validation(df: pd.DataFrame, fee_rate: float, timeframe: str, train_ratio: float=.70):
    cut=max(1,int(len(df)*train_ratio))
    train,tm=analyze(df.iloc[:cut].copy(),fee_rate,timeframe)
    test,vm=analyze(df.iloc[cut:].copy(),fee_rate,timeframe)
    return train,tm,test,vm
