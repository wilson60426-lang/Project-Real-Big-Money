"""Offline tests for exact-session SPY comparison; no Yahoo requests."""
import pandas as pd
import pytest

from analytics.market_context import (
    with_spy_context, market_context_commentary, fetch_spy_daily_prices,
)
from analytics.earnings_reactions import align_earnings_reactions


NOW="2026-08-10T18:00:00Z"


def bars(dates, closes):
    return pd.DataFrame({
        "timestamp": pd.to_datetime(dates),
        "open": [price-1 for price in closes],
        "high": [price+2 for price in closes],
        "low": [price-3 for price in closes],
        "close": closes,
        "volume": [1000]*len(closes),
    })


def earnings_event(ts, reported=1.3):
    return pd.DataFrame([{
        "announcement_date": ts, "eps_estimate": 1.0,
        "eps_reported": reported, "eps_surprise_pct": 30.0,
    }])


def sample_reaction():
    stock = bars(["2026-07-29","2026-07-30","2026-07-31"],[99,100,110])
    events = earnings_event("2026-07-30T21:00:00Z")
    reaction = align_earnings_reactions(stock, events, now=NOW)
    assert reaction.iloc[0]["status"] == "可觀察（非因果）"
    return reaction


def test_exact_window_compares_stock_to_spy_in_percentage_points():
    spy = bars(["2026-07-29","2026-07-30","2026-07-31"],[210,200,204])
    out = with_spy_context(sample_reaction(), spy, now=NOW)
    row = out.iloc[0]
    assert row["spy_baseline_close"] == 200
    assert row["spy_reaction_close"] == 204
    assert row["spy_close_to_close_pct"] == pytest.approx(2)
    assert row["relative_to_spy_pp"] == pytest.approx(8)
    assert row["market_context_status"] == "有相同交易日"
    comment=market_context_commentary(row)
    assert "百分點" in comment
    assert "不能證明" in comment


def test_missing_exact_baseline_does_not_forward_fill():
    spy=bars(["2026-07-29","2026-07-31"],[200,204])
    row=with_spy_context(sample_reaction(),spy,now=NOW).iloc[0]
    assert row["market_context_status"] == "SPY 資料不足"
    assert pd.isna(row["relative_to_spy_pp"])


def test_missing_exact_end_date_does_not_use_future_date():
    spy=bars(["2026-07-30","2026-08-03"],[200,210])
    row=with_spy_context(sample_reaction(),spy,now=NOW).iloc[0]
    assert row["market_context_status"] == "SPY 資料不足"
    assert pd.isna(row["spy_close_to_close_pct"])


def test_empty_or_missing_benchmark_does_not_fabricate_outperformance():
    for missing in (None,pd.DataFrame()):
        row=with_spy_context(sample_reaction(),missing,now=NOW).iloc[0]
        assert pd.isna(row["relative_to_spy_pp"])
        assert row["market_context_status"] == "SPY 資料不足"


def test_uncertain_stock_event_is_not_compared():
    reaction = sample_reaction()
    reaction.loc[0,"status"]="不可計算"
    out=with_spy_context(reaction,bars(["2026-07-30","2026-07-31"],[200,204]),now=NOW)
    assert out.iloc[0]["market_context_status"] == "未比較"
    assert pd.isna(out.iloc[0]["relative_to_spy_pp"])


def test_incomplete_benchmark_daily_candle_is_excluded():
    spy=bars(["2026-07-30","2026-07-31"],[200,204])
    # July 31, 2026 14:00 ET => daily candle not closed yet.
    row=with_spy_context(sample_reaction(),spy,now="2026-07-31T18:00:00Z").iloc[0]
    assert row["market_context_status"] == "SPY 資料不足"


def test_zero_benchmark_price_is_rejected():
    spy=bars(["2026-07-30","2026-07-31"],[200,0])
    row=with_spy_context(sample_reaction(),spy,now=NOW).iloc[0]
    assert pd.isna(row["relative_to_spy_pp"])


def test_empty_reactions_preserve_schema():
    output=with_spy_context(pd.DataFrame(columns=["status"]),None,now=NOW)
    assert output.empty
    assert "relative_to_spy_pp" in output.columns


class FakeTicker:
    def __init__(self,symbol):
        assert symbol=="SPY"
    def history(self,**kwargs):
        assert kwargs["auto_adjust"] is False
        return bars(["2026-07-30","2026-07-31"],[200,204])


def test_spy_fetch_has_testable_provider():
    result=fetch_spy_daily_prices(ticker_factory=FakeTicker,now=NOW)
    assert len(result)==2
    assert list(result["close"])==[200,204]
