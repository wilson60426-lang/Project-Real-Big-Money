import numpy as np
import pandas as pd

def _periods_per_year(aligned):
    if "date" not in aligned.columns or len(aligned)<2:
        return 252.0
    days=(pd.to_datetime(aligned["date"].iloc[-1])-pd.to_datetime(aligned["date"].iloc[0])).days
    if days<=0: return 252.0
    return float(max(1,min(366,(len(aligned)-1)/(days/365.25))))

def annualized_stats(aligned):
    if aligned.empty: return {}
    ppy=_periods_per_year(aligned)
    out={}
    for key in ["a","b"]:
        r=aligned[key].dropna()
        if len(r)<2: return {}
        vol=float(r.std()*np.sqrt(ppy))
        annual=float((1+r).prod()**(ppy/max(len(r),1))-1)
        sharpe=float(r.mean()/r.std()*np.sqrt(ppy)) if r.std()>0 else 0.0
        eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
        out[key]={"annual_return":annual,"volatility":vol,"sharpe":sharpe,"max_drawdown":float(dd.min())}
    out["correlation"]=float(aligned["a"].corr(aligned["b"]))
    return out

def rolling_correlation(aligned,window=30):
    d=aligned.copy(); d["rolling_corr"]=d["a"].rolling(window).corr(d["b"]); return d

def normalized_growth(aligned):
    d=aligned.copy(); d["A"]=(1+d["a"]).cumprod(); d["B"]=(1+d["b"]).cumprod(); return d

def diversification_score(corr):
    if np.isnan(corr): return 0,"資料不足"
    score=int(round(max(0,min(100,(1-corr)/2*100))))
    label="分散效果較高" if score>=60 else "有一些分散效果" if score>=35 else "分散效果有限"
    return score,label
