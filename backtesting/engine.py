import pandas as pd


def backtest(df: pd.DataFrame, fee_rate: float = 0.001) -> dict:
    data = df.dropna().copy()
    data["return"] = data["close"].pct_change().fillna(0)
    data["position"] = data["signal"].shift(1).fillna(0)
    trades = data["position"].diff().abs().fillna(0)
    data["strategy_return"] = data["position"] * data["return"] - trades * fee_rate
    equity = (1 + data["strategy_return"]).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1
    return {"total_return": float(equity.iloc[-1] - 1) if len(equity) else 0.0,
            "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
            "trades": int((trades > 0).sum())}
