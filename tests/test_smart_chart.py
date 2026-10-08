import pandas as pd
from indicators.basic import add_indicators
from charts.workbench import describe_indicators
from backtesting.validation import regime_report
from backtesting.analytics import analyze
from alerts.engine import entry_score

def fixture(n=280):
    t=pd.date_range("2024-01-01",periods=n,freq="D")
    close=pd.Series([100+i*.12+((i%17)-8)*.25 for i in range(n)],dtype=float)
    return pd.DataFrame({"timestamp":t,"open":close-.3,"high":close+1,"low":close-1,"close":close,"volume":1000,"signal":1})

def test_smart_indicators_exist_and_bands_ordered():
    d=add_indicators(fixture())
    for col in ("ema_12","ema_26","macd","macd_signal","macd_hist","bb_upper","bb_lower","atr_14"):
        assert col in d.columns
        assert pd.notna(d[col].iloc[-1])
    assert d["bb_upper"].iloc[-1]>=d["bb_lower"].iloc[-1]
    assert d["atr_14"].iloc[-1]>0

def test_beginner_explanations_are_available():
    _,messages=describe_indicators(fixture())
    assert len(messages)>=4
    assert any("ATR" in message for message in messages)

def test_regime_report_preserves_original_returns():
    d=fixture()
    d["signal"]=[1 if i%31<18 else 0 for i in range(len(d))]
    full,_=analyze(d,0.001,"1d")
    regimes=regime_report(d,0.001,"1d")
    assert len(regimes)>0
    assert regimes["K線數"].sum()<=len(full)

def test_initial_position_turnover_is_charged():
    d=fixture(10)
    result,_=analyze(d,0.01,"1d")
    assert result["turnover"].iloc[1]==1
    assert result["strategy_return"].iloc[1] < result["market_return"].iloc[1]

def test_no_price_trigger_gives_no_forty_point_bonus():
    score,_,_,_=entry_score(False,1,35,None,True)
    assert score==45
