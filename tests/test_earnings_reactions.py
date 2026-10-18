"""No-network regression tests for US earnings-time / daily-close mapping."""
import pandas as pd
import pytest

from analytics.earnings_reactions import (
    align_earnings_reactions,
    normalize_equity_prices,
    reaction_commentary,
)
from charts.earnings_workbench import make_earnings_chart


def daily(dates, closes=None):
    if closes is None:
        closes=[100.0+i*2 for i in range(len(dates))]
    return pd.DataFrame({
        "timestamp":pd.to_datetime(dates),
        "open":[c-1 for c in closes],
        "high":[c+2 for c in closes],
        "low":[c-3 for c in closes],
        "close":closes,
        "volume":[1000 for _ in closes],
    })


def eps_events(*timestamps, reported=1.2):
    return pd.DataFrame({
        "announcement_date":list(timestamps),
        "eps_estimate":[1.0 for _ in timestamps],
        "eps_reported":[reported for _ in timestamps],
        "eps_surprise_pct":[20.0 for _ in timestamps],
        "state":["已公布" for _ in timestamps],
    })


NOW="2026-08-06T18:00:00Z"
BARS=daily(["2026-07-29","2026-07-30","2026-07-31","2026-08-03","2026-08-04"],[100,102,110,109,112])


def test_afterhours_earnings_moves_next_trading_session():
    events=eps_events("2026-07-30T21:00:00+00:00") # 17:00 ET
    results=align_earnings_reactions(BARS,events,now=NOW)
    event=results.iloc[0]
    assert event["timing"]=="盤後"
    assert event["baseline_date"]=="2026-07-30"
    assert event["reaction_date"]=="2026-07-31"
    assert event["close_to_close_pct"]==pytest.approx((110/102-1)*100)
    assert event["status"]=="可觀察（非因果）"
    assert "不能認定" in reaction_commentary(event)


def test_beforehours_earnings_use_prior_close_and_same_day_close():
    events=eps_events("2026-07-30T11:00:00+00:00") # 07:00 ET
    event=align_earnings_reactions(BARS,events,now=NOW).iloc[0]
    assert event["timing"]=="盤前"
    assert event["baseline_date"]=="2026-07-29"
    assert event["reaction_date"]=="2026-07-30"
    assert event["close_to_close_pct"]==pytest.approx(2.0)


def test_weekend_event_uses_first_next_completed_session_not_weekend():
    events=eps_events("2026-08-01T14:00:00Z") # Sat 10:00 ET
    event=align_earnings_reactions(BARS,events,now=NOW).iloc[0]
    assert event["timing"]=="非交易日公布"
    assert event["baseline_date"]=="2026-07-31"
    assert event["reaction_date"]=="2026-08-03"


@pytest.mark.parametrize("when",[
    "2026-07-30T14:00:00Z",  # 10:00 ET intraday
    "2026-07-30T15:59:00-04:00", # intraday
    "2026-07-30T00:00:00Z",  # plausible date-only midnight placeholder
    "2026-07-30T21:00:00",  # no timezone
])
def test_unknown_or_intraday_timing_is_not_given_price_attribution(when):
    event=align_earnings_reactions(BARS,eps_events(when),now=NOW).iloc[0]
    assert event["status"]=="不可計算"
    assert pd.isna(event["close_to_close_pct"])


def test_future_or_missing_reported_eps_not_attributed():
    results=align_earnings_reactions(
        BARS,eps_events("2026-12-30T21:00:00Z"),now=NOW
    )
    assert results.iloc[0]["status"]=="不可計算"
    blank=align_earnings_reactions(
        BARS,eps_events("2026-07-30T21:00:00Z",reported=None),now=NOW
    )
    assert blank.iloc[0]["status"]=="不可計算"


def test_incomplete_today_daily_bar_not_counted_even_when_present():
    bars=daily(["2026-07-30","2026-07-31"],[100,120])
    # 2026-07-31 15:00 ET -- not finished
    event=align_earnings_reactions(
        bars,eps_events("2026-07-30T21:00:00Z"),
        now="2026-07-31T19:00:00Z",
    ).iloc[0]
    assert event["status"]=="不可計算"
    assert pd.isna(event["reaction_close"])


def test_normalize_excludes_future_prices_and_bad_zero():
    bars=daily(["2026-07-30","2026-07-31","2026-08-07"],[100,0,200])
    rows=normalize_equity_prices(bars,now=NOW)
    assert len(rows)==1
    assert rows.iloc[0]["session_date"].isoformat()=="2026-07-30"


def test_missing_trading_day_gaps_do_not_make_false_event_return():
    bars=daily(["2026-07-01","2026-07-20"],[100,130])
    event=align_earnings_reactions(
        bars,eps_events("2026-07-18T14:00:00Z"),now=NOW
    ).iloc[0]
    assert event["status"]=="不可計算"


def test_daylight_savings_transitions_are_resolved_by_zone():
    bars=daily(["2026-11-02","2026-11-03"],[100,102])
    event=align_earnings_reactions(
        bars,eps_events("2026-11-02T22:00:00+00:00"),
        now="2026-11-06T18:00:00Z"
    ).iloc[0]
    assert event["timing"]=="盤後"
    assert event["baseline_date"]=="2026-11-02"
    assert event["reaction_date"]=="2026-11-03"


def test_plotting_chart_only_marks_earnings_dates_with_reported_eps():
    fig,count=make_earnings_chart(
        BARS,eps_events("2026-07-30T21:00:00Z"),"NVDA"
    )
    assert fig is not None
    assert count==1
    assert any(trace.type=="candlestick" for trace in fig.data)
    blank_fig,count=make_earnings_chart(
        BARS,eps_events("2026-07-30T21:00:00Z",reported=None),"NVDA"
    )
    assert blank_fig is not None
    assert count==0


def test_missing_weekday_price_is_not_assumed_to_be_market_holiday():
    bars=daily(["2026-07-29","2026-07-31"],[100,102])
    event=align_earnings_reactions(
        bars,eps_events("2026-07-30T21:00:00Z"),now=NOW
    ).iloc[0]
    assert event["status"]=="不可計算"
    assert "交易日資料缺漏" in event["timing"]
