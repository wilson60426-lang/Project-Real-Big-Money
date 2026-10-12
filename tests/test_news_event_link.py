from datetime import datetime, timezone
import pandas as pd
from news.event_link import relevant_news, event_reactions

def candles():
    return pd.DataFrame({
        "timestamp":pd.date_range("2026-10-01",periods=5,freq="D"),
        "open":[100,101,102,103,104],
        "close":[101,102,103,104,105],
    })

def item(title,published):
    return {"title":title,"url":"https://example.com/article","source":"測試來源",
            "published":datetime.fromisoformat(published).replace(tzinfo=timezone.utc)}

def test_relevant_news_matches_symbol_without_unrelated_titles():
    news=[item("Bitcoin rises","2026-10-01T12:00:00"),item("Apple earnings","2026-10-01T12:00:00")]
    assert len(relevant_news(news,"BTC/USDT"))==1

def test_event_only_uses_candles_after_publication():
    news=[item("Bitcoin rises","2026-10-01T12:00:00")]
    results=event_reactions(candles(),news,timeframe="1d",now="2026-10-10T00:00:00Z")
    assert len(results)==1
    assert results[0]["candle_time"]==pd.Timestamp("2026-10-02",tz="UTC")

def test_unfinished_candle_is_excluded():
    news=[item("Bitcoin rises","2026-10-04T12:00:00")]
    results=event_reactions(candles(),news,timeframe="1d",now="2026-10-05T12:00:00Z")
    assert results==[]
