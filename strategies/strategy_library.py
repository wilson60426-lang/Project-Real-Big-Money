import pandas as pd

def sma_cross(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy(); out["signal"]=0
    out.loc[out["sma_20"]>out["sma_50"],"signal"]=1
    out.loc[out["sma_20"]<out["sma_50"],"signal"]=-1
    return out

def rsi_reversion(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy(); out["signal"]=0
    # Long-only mean reversion: enter oversold, stay flat otherwise.
    out.loc[out["rsi_14"]<30,"signal"]=1
    return out

def trend_rsi(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy(); out["signal"]=0
    out.loc[(out["sma_20"]>out["sma_50"]) & (out["rsi_14"]>=50),"signal"]=1
    out.loc[(out["sma_20"]<out["sma_50"]) & (out["rsi_14"]<=50),"signal"]=-1
    return out

STRATEGIES={"SMA Cross":sma_cross,"RSI Reversion":rsi_reversion,"Trend + RSI":trend_rsi}
