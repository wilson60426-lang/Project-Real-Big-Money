import time
import pandas as pd
import ccxt

def fetch_history(exchange_name="binance", symbol="BTC/USDT", timeframe="1h", years=3, batch_limit=1000):
    exchange=getattr(ccxt,exchange_name)({"enableRateLimit":True})
    now=exchange.milliseconds()
    since=now-int(years*365.25*24*60*60*1000)
    rows=[]
    while since < now:
        batch=exchange.fetch_ohlcv(symbol,timeframe,since=since,limit=batch_limit)
        if not batch: break
        rows.extend(batch)
        nxt=batch[-1][0]+1
        if nxt<=since: break
        since=nxt
        if len(batch)<batch_limit: break
        time.sleep(exchange.rateLimit/1000)
    if not rows: return pd.DataFrame(columns=["timestamp","open","high","low","close","volume"])
    df=pd.DataFrame(rows,columns=["timestamp","open","high","low","close","volume"])
    df=df.drop_duplicates("timestamp").sort_values("timestamp")
    df["timestamp"]=pd.to_datetime(df["timestamp"],unit="ms")
    return df.reset_index(drop=True)
