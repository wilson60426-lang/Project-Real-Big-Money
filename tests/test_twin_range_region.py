import pandas as pd
from indicators.twin_range import twin_range_filter
from charts.region_analysis import explain_region
from charts.workbench import make_chart

def sample(n=220):
    close=pd.Series([100+i*.15+((i%9)-4)*.3 for i in range(n)],dtype=float)
    return pd.DataFrame({"timestamp":pd.date_range("2026-01-01",periods=n,freq="h"),
      "open":close-.1,"high":close+1,"low":close-1,"close":close,"volume":1000})

def test_trf_has_warmup_and_no_future_values():
    d=sample()
    full=twin_range_filter(d)
    prefix=twin_range_filter(d.iloc[:180])
    assert full["trf_filter"].iloc[:180].equals(prefix["trf_filter"])
    assert full["trf_filter"].notna().sum()>0

def test_region_explanation_and_chart():
    d=sample()
    messages=explain_region(d,120,150)
    assert len(messages)>=3
    fig,_=make_chart(d,"TEST",show_trf=True)
    assert any(t.name=="Twin Range Filter" for t in fig.data)
    assert any(t.name=="框選 K 線" for t in fig.data)
