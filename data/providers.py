import pandas as pd
import yfinance as yf
from data.history import fetch_history

CRYPTO={"BTC":"BTC/USDT","ETH":"ETH/USDT","SOL":"SOL/USDT"}
EQUITIES=["SPY","QQQ","IWM","AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"]

def get_asset(asset, asset_type, years=3, timeframe="1d"):
    if asset_type=="Crypto":
        return fetch_history("binance",CRYPTO.get(asset,asset),timeframe if timeframe in ["1h","4h","1d"] else "1d",years)
    end=pd.Timestamp.now(tz="UTC").tz_localize(None)+pd.Timedelta(days=1)
    start=end-pd.DateOffset(years=years)-pd.Timedelta(days=10)
    df=yf.download(asset,start=start.date(),end=end.date(),interval="1d",auto_adjust=True,actions=False,progress=False,threads=False)
    if df.empty:
        return pd.DataFrame(columns=["timestamp","open","high","low","close","volume"])
    if isinstance(df.columns,pd.MultiIndex):
        df.columns=df.columns.get_level_values(0)
    df=df.reset_index().rename(columns={"Date":"timestamp","Datetime":"timestamp","Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    ts=pd.to_datetime(df["timestamp"])
    if getattr(ts.dt,"tz",None) is not None:
        ts=ts.dt.tz_localize(None)
    df["timestamp"]=ts
    cutoff=end-pd.DateOffset(years=years)
    df=df[df["timestamp"]>=cutoff]
    return df[["timestamp","open","high","low","close","volume"]].dropna(subset=["close"]).reset_index(drop=True)

def _daily_close(df,name):
    if df.empty:
        return pd.DataFrame(columns=["date",name])
    x=df[["timestamp","close"]].copy()
    x["date"]=pd.to_datetime(x["timestamp"]).dt.date
    return x.groupby("date",as_index=False)["close"].last().rename(columns={"close":name})

def daily_returns(df):
    x=_daily_close(df,"close")
    x["return"]=x["close"].pct_change()
    return x.dropna()

def align_returns(a,b):
    # Align prices first, then calculate returns. This makes Friday→Monday
    # intervals comparable when one asset trades through the weekend.
    d=_daily_close(a,"a_close").merge(_daily_close(b,"b_close"),on="date",how="inner").dropna()
    d["a"]=d["a_close"].pct_change()
    d["b"]=d["b_close"].pct_change()
    return d.dropna().reset_index(drop=True)
