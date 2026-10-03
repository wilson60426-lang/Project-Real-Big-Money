import pandas as pd


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["signal"] = 0
    out.loc[out["sma_20"] > out["sma_50"], "signal"] = 1
    out.loc[out["sma_20"] < out["sma_50"], "signal"] = -1
    return out
