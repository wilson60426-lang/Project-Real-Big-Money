import numpy as np
import pandas as pd
from analytics.cross_asset import annualized_stats, diversification_score
from backtesting.trade_engine import trade_statistics
from backtesting.challenge import bootstrap_expectancy, monte_carlo_drawdown

def test_diversification_score_bounds():
    for c in [-1,0,.5,1]:
        score,_=diversification_score(c); assert 0<=score<=100

def test_cross_asset_stats_identical_series():
    r=np.array([.01,-.005,.002,.004,-.003]*20); df=pd.DataFrame({"a":r,"b":r})
    assert abs(annualized_stats(df)["correlation"]-1)<1e-9

def test_trade_statistics_true_win_rate():
    t=pd.DataFrame({"淨報酬":[.1,-.05,.02,-.01],"持有K線數":[2,3,4,5],"MAE":[-.02,-.06,-.01,-.03],"MFE":[.12,.01,.03,.01]})
    s=trade_statistics(t); assert s["trades"]==4; assert s["win_rate"]==.5; assert s["max_consecutive_losses"]==1

def test_bootstrap_is_reproducible():
    t=pd.DataFrame({"淨報酬":[.01,.02,-.005,.015]})
    assert bootstrap_expectancy(t,n=100,seed=7)==bootstrap_expectancy(t,n=100,seed=7)

def test_monte_carlo_drawdown_non_positive():
    t=pd.DataFrame({"淨報酬":[.02,-.01,.01,-.03,.04]})
    x=monte_carlo_drawdown(t,n=100,seed=1); assert x["median_max_dd"]<=0; assert x["p95_worst_dd"]<=0
