import ccxt
import pandas as pd


def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
    exchange_cls = getattr(ccxt, exchange_name)
    exchange = exchange_cls({"enableRateLimit": True})
    rows = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df
