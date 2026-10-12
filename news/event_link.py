"""Conservative news-to-chart matching. Never interpret association as causation."""
from datetime import timezone
import pandas as pd

KEYWORDS={
    "BTC/USDT":("bitcoin","btc","比特幣"),
    "ETH/USDT":("ethereum","ether","eth","以太幣"),
    "SOL/USDT":("solana","sol","索拉納"),
    "AAPL":("apple","aapl","蘋果公司"),
    "NVDA":("nvidia","nvda","輝達","英偉達"),
    "SPY":("s&p 500","sp500","標普500","美股"),
    "QQQ":("nasdaq","納斯達克","科技股"),
    "2330.TW":("台積電","tsmc","2330"),
    "0050.TW":("0050","元大台灣50"),
    "2317.TW":("鴻海","foxconn","2317"),
    "2454.TW":("聯發科","mediatek","2454"),
}

def relevant_news(items,symbol):
    import re
    terms=KEYWORDS.get(symbol,())
    result=[]
    for item in items:
        title=item.get("title","").casefold()
        if any(re.search(r"(?<![a-z0-9])"+re.escape(t.casefold())+r"(?![a-z0-9])",title) for t in terms):
            result.append(item)
    return result

def event_reactions(df,items,limit=12):
    """Map to first candle starting on/after publication; only compare completed bars.
    For daily equity candles the calendar-day mapping is illustrative, not intraday attribution.
    """
    d=df.copy().sort_values("timestamp")
    if len(d)<3: return []
    times=pd.to_datetime(d["timestamp"],utc=True)
    out=[]
    for item in items:
        published=item.get("published")
        if published is None: continue
        stamp=pd.Timestamp(published)
        if stamp.tzinfo is None: stamp=stamp.tz_localize("UTC")
        else: stamp=stamp.tz_convert("UTC")
        future=times[times>=stamp]
        if future.empty: continue
        idx=future.index[0]
        loc=d.index.get_loc(idx)
        if not isinstance(loc,int) or loc+1>=len(d): continue
        base=float(d.iloc[loc]["open"])
        later=float(d.iloc[loc]["close"])
        if base<=0: continue
        out.append({"title":item["title"],"url":item["url"],"source":item["source"],
                    "published":stamp,"candle_time":times.loc[idx],
                    "candle_return":later/base-1})
        if len(out)>=limit: break
    return out
