import pandas as pd
import yfinance as yf
from data.history import fetch_history

CRYPTO={"BTC":"BTC/USDT","ETH":"ETH/USDT","SOL":"SOL/USDT"}
EQUITIES=["SPY","QQQ","IWM","AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"]

def get_asset(asset, asset_type, years=3, timeframe="1d"):
    if asset_type=="Crypto":
        return fetch_history("binance",CRYPTO.get(asset,asset),timeframe if timeframe in ["1h","4h","1d"] else "1d",years)
    period=f"{years}y" if years in [1,2,5] else "5y"
    df=yf.download(asset,period=period,interval="1d",auto_adjust=True,progress=False,threads=False)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns,pd.MultiIndex):
        df.columns=df.columns.get_level_values(0)
    df=df.reset_index().rename(columns={"Date":"timestamp","Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    df["timestamp"]=pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    if years==3:
        df=df[df["timestamp"]>=df["timestamp"].max()-pd.DateOffset(years=3)]
    return df[["timestamp","open","high","low","close","volume"]].dropna().reset_index(drop=True)

def daily_returns(df):
    if df.empty:
        return pd.DataFrame(columns=["date","close","return"])
    x=df[["timestamp","close"]].copy()
    x["date"]=pd.to_datetime(x["timestamp"]).dt.date
    x=x.groupby("date",as_index=False)["close"].last()
    x["return"]=x["close"].pct_change()
    return x.dropna()

def align_returns(a,b):
    x=daily_returns(a).rename(columns={"return":"a","close":"a_close"})
    y=daily_returns(b).rename(columns={"return":"b","close":"b_close"})
    return x.merge(y,on="date",how="inner")
