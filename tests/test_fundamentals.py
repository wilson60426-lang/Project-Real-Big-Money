"""Offline financial statement parsing tests; never contact Yahoo Finance."""
import pandas as pd
import pytest

from data.fundamentals import (
    extract_quarterly_income,
    extract_eps_consensus,
    fetch_us_financials,
    explain_report,
)


def _quarterly():
    return pd.DataFrame({
        pd.Timestamp("2026-06-30"): [120e9, 48e9, 33e9, 27e9, 1.23],
        pd.Timestamp("2026-03-31"): [110e9, 40e9, 29e9, 23e9, 1.11],
        pd.Timestamp("2025-06-30"): [100e9, 35e9, 24e9, 18e9, 0.88],
        pd.Timestamp("2025-03-31"): [90e9, 30e9, 20e9, 14e9, 0.75],
    }, index=["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Diluted EPS"])


def test_quarterly_statement_and_yoy_based_on_matching_fiscal_period():
    result=extract_quarterly_income(_quarterly())
    assert len(result)==4
    assert result.iloc[0]["period_end"]=="2026-06-30"
    assert result.iloc[0]["revenue"]==120e9
    assert result.iloc[0]["gross_margin_pct"]==pytest.approx(40)
    assert result.iloc[0]["revenue_yoy_pct"]==pytest.approx(20)
    assert result.iloc[1]["revenue_yoy_pct"]==pytest.approx(100*(110/90-1))
    assert pd.isna(result.iloc[-1]["revenue_yoy_pct"])
    assert result.iloc[0]["statement_eps"]==1.23


def test_missing_or_zero_denominator_does_not_invent_margin_or_growth():
    frame=pd.DataFrame({
        pd.Timestamp("2026-06-30"): [0.0, None],
        pd.Timestamp("2025-06-30"): [0.0, None],
    }, index=["Total Revenue","Gross Profit"])
    result=extract_quarterly_income(frame)
    assert pd.isna(result.iloc[0]["gross_margin_pct"])
    assert pd.isna(result.iloc[0]["revenue_yoy_pct"])
    assert pd.isna(result.iloc[0]["statement_eps"])
    assert extract_quarterly_income(pd.DataFrame()).empty


def test_eps_surprise_uses_announcement_pairs_and_not_past_quarter_index():
    dates=pd.DatetimeIndex(["2026-07-30T21:00:00Z","2026-04-29T21:00:00Z"])
    frame=pd.DataFrame({"EPS Estimate":[1.00,1.20],
                        "Reported EPS":[1.25,1.00]},index=dates)
    result=extract_eps_consensus(frame,as_of="2026-08-01T00:00:00Z")
    assert len(result)==2
    assert result.iloc[0]["eps_surprise_pct"]==pytest.approx(25)
    assert result.iloc[1]["eps_surprise_pct"]==pytest.approx(-100/6)


def test_future_eps_cannot_be_reported_and_zero_consensus_has_no_percentage():
    dates=pd.DatetimeIndex(["2026-11-01T00:00:00Z","2026-06-01T00:00:00Z"])
    frame=pd.DataFrame({"EPS Estimate":[2.0,0.0],
                        "Reported EPS":[99.0,0.20]},index=dates)
    result=extract_eps_consensus(frame,as_of="2026-08-01T00:00:00Z")
    assert pd.isna(result.iloc[0]["eps_reported"])
    assert pd.isna(result.iloc[0]["eps_surprise_pct"])
    assert pd.isna(result.iloc[1]["eps_surprise_pct"])
    assert "尚無" in result.iloc[0]["state"]


def test_missing_eps_estimate_and_only_reported_does_not_fake_surprise():
    frame=pd.DataFrame({
        "EPS Estimate":[float("nan")],
        "Reported EPS":[1.25],
    },index=pd.DatetimeIndex(["2026-07-30T21:00:00Z"]))
    result=extract_eps_consensus(frame,as_of="2026-08-01T00:00:00Z")
    assert pd.isna(result.iloc[0]["eps_surprise_pct"])
    assert "無可比" in result.iloc[0]["state"]


class FakeTicker:
    def __init__(self,symbol):
        self.symbol=symbol
    @property
    def quarterly_income_stmt(self):
        return _quarterly()
    def get_earnings_dates(self,limit=12):
        assert limit==12
        return pd.DataFrame({
            "EPS Estimate":[1.0],"Reported EPS":[1.2],
        },index=pd.DatetimeIndex(["2026-07-30T21:00:00Z"]))
    @property
    def info(self):
        return {"financialCurrency":"USD"}


class MissingTicker(FakeTicker):
    @property
    def quarterly_income_stmt(self):
        raise RuntimeError("no report")
    def get_earnings_dates(self,limit=12):
        raise RuntimeError("not available")
    @property
    def info(self):
        raise RuntimeError("no currency")


def test_fetch_financials_keeps_provenance_and_partial_failure():
    report=fetch_us_financials("AAPL",ticker_factory=FakeTicker,now=pd.Timestamp("2026-08-01T00:00:00Z"))
    assert report["currency"]=="USD"
    assert not report["quarterly"].empty
    assert report["eps_events"].iloc[0]["eps_surprise_pct"]==pytest.approx(20)
    assert "毛利率" in " ".join(explain_report(report))
    failed=fetch_us_financials("NVDA",ticker_factory=MissingTicker,now=pd.Timestamp("2026-08-01T00:00:00Z"))
    assert failed["quarterly"].empty
    assert failed["eps_events"].empty
    assert failed["currency"] is None
    assert len(failed["notes"])>=3


def test_only_equities_supported_not_etfs_or_crypto():
    for symbol in ("SPY","QQQ","BTC/USDT","2330.TW","NOTAREALSYMBOL"):
        with pytest.raises(ValueError):
            fetch_us_financials(symbol,ticker_factory=FakeTicker)


def test_no_forward_fill_or_guess_of_consensus():
    assert extract_eps_consensus(None).empty
    assert extract_quarterly_income(None).empty
