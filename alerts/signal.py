from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.challenge import challenge_strategy

def analyze_entry_candidate(raw, strategy_name="Trend + RSI", fee=0.001, slippage=0.0005, timeframe="1d", run_challenge=False):
    d=add_indicators(raw)
    sig=STRATEGIES[strategy_name](d)
    if sig.empty:
        return {"signal":0,"rsi":None,"trend_up":None,"challenge_score":None}
    row=sig.iloc[-1]
    rsi=None if row["rsi_14"]!=row["rsi_14"] else float(row["rsi_14"])
    trend_up=None
    if row["sma_20"]==row["sma_20"] and row["sma_50"]==row["sma_50"]:
        trend_up=bool(row["sma_20"]>row["sma_50"])
    challenge_score=None
    if run_challenge and len(sig)>=250:
        challenge_score=int(challenge_strategy(sig,fee,timeframe,slippage)["score"])
    return {
        "signal":int(row["signal"]),
        "rsi":rsi,
        "trend_up":trend_up,
        "challenge_score":challenge_score
    }
