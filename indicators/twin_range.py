"""Twin Range Filter: an explicitly documented, non-proprietary approximation.

Two smoothed absolute close changes are averaged into a dynamic price range.
A recursive filter follows price only when the change exceeds that range.
This is a research implementation; settings may differ from TradingView scripts.
"""
import numpy as np
import pandas as pd

def twin_range_filter(df, fast_period=27, fast_multiplier=1.6, slow_period=55, slow_multiplier=2.0):
    if fast_period<2 or slow_period<2 or fast_multiplier<=0 or slow_multiplier<=0:
        raise ValueError("週期至少為 2，倍率必須大於 0")
    out=df.copy()
    close=pd.to_numeric(out["close"],errors="coerce")
    change=close.diff().abs()
    def smooth(period,multiplier):
        first=change.ewm(span=period,adjust=False,min_periods=period).mean()
        return first.ewm(span=2*period-1,adjust=False,min_periods=2*period-1).mean()*multiplier
    width=(smooth(fast_period,fast_multiplier)+smooth(slow_period,slow_multiplier))/2
    out["trf_range"]=width
    filt=np.full(len(out),np.nan)
    direction=np.zeros(len(out),dtype=int)
    previous=np.nan
    for i,(price,rng) in enumerate(zip(close.to_numpy(),width.to_numpy())):
        if not np.isfinite(price) or not np.isfinite(rng): continue
        if not np.isfinite(previous):
            previous=price
        elif price>previous:
            previous=max(previous,price-rng)
        elif price<previous:
            previous=min(previous,price+rng)
        filt[i]=previous
        if i and np.isfinite(filt[i-1]):
            direction[i]=1 if filt[i]>filt[i-1] else -1 if filt[i]<filt[i-1] else direction[i-1]
    out["trf_filter"]=filt
    out["trf_direction"]=direction
    out["trf_long_setup"]=(close>out["trf_filter"])&(out["trf_direction"]==1)
    out["trf_short_setup"]=(close<out["trf_filter"])&(out["trf_direction"]==-1)
    return out
