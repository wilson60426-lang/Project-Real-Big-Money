"""Like-for-like SPY context for completed US earnings event windows.

This computes an *arithmetic return difference*, not a risk-adjusted abnormal
return and never a causal earnings impact. SPY is a proxy for the broad US
market, not a sector-matched benchmark. The calendar windows must be EXACT.
"""
import pandas as pd
import yfinance as yf

from analytics.earnings_reactions import normalize_equity_prices

BENCHMARK_SYMBOL = "SPY"
BENCHMARK_DESCRIPTION = "SPY（SPDR 標普 500 ETF）"
CONTEXT_COLUMNS = (
    "spy_baseline_close", "spy_reaction_close",
    "spy_close_to_close_pct", "relative_to_spy_pp",
    "market_context_status", "market_context_note",
)


def fetch_spy_daily_prices(ticker_factory=None, now=None):
    """Fetch unadjusted SPY daily prices; optional factory for offline tests."""
    factory = ticker_factory or yf.Ticker
    raw = factory(BENCHMARK_SYMBOL).history(
        period="2y", interval="1d", auto_adjust=False, actions=False
    )
    return normalize_equity_prices(raw, now=now)


def with_spy_context(reactions, spy_prices, now=None):
    """Attach SPY returns ONLY for exact matching completed session dates.

    There is intentionally no forward-fill, nearest-date lookup, or
    substitution with an unrelated trading day.
    """
    if not isinstance(reactions, pd.DataFrame):
        raise TypeError("reactions 必須是 DataFrame")
    result = reactions.copy()
    for column in CONTEXT_COLUMNS:
        if column in ("market_context_status", "market_context_note"):
            result[column] = ""
        else:
            result[column] = float("nan")
    if result.empty:
        return result

    try:
        spy = normalize_equity_prices(spy_prices, now=now)
    except (ValueError, TypeError, KeyError):
        spy = pd.DataFrame()
    by_date = spy.set_index("session_date") if not spy.empty else pd.DataFrame()

    for idx, row in result.iterrows():
        if row.get("status") != "可觀察（非因果）":
            result.at[idx, "market_context_status"] = "未比較"
            result.at[idx, "market_context_note"] = "個股事件尚無可靠的完成日 K，不能計算市場相對變動。"
            continue
        start = row.get("baseline_date")
        end = row.get("reaction_date")
        if not start or not end:
            result.at[idx, "market_context_status"] = "缺少日期"
            result.at[idx, "market_context_note"] = "個股對照窗口不完整。"
            continue
        try:
            start_date = pd.Timestamp(start).date()
            end_date = pd.Timestamp(end).date()
        except (ValueError,TypeError,OverflowError):
            result.at[idx, "market_context_status"] = "日期無效"
            result.at[idx, "market_context_note"] = "無法辨識個股交易日期。"
            continue
        if start_date >= end_date or by_date.empty or start_date not in by_date.index or end_date not in by_date.index:
            result.at[idx, "market_context_status"] = "SPY 資料不足"
            result.at[idx, "market_context_note"] = "SPY 缺少相同起訖已完成交易日，禁止用鄰近日補值。"
            continue
        before = pd.to_numeric(by_date.loc[start_date, "close"], errors="coerce")
        after = pd.to_numeric(by_date.loc[end_date, "close"], errors="coerce")
        stock_pct = pd.to_numeric(row.get("close_to_close_pct"),errors="coerce")
        if pd.isna(before) or pd.isna(after) or pd.isna(stock_pct) or float(before) <= 0 or float(after) <= 0:
            result.at[idx, "market_context_status"] = "價格無效"
            result.at[idx, "market_context_note"] = "SPY 或個股收盤價無效，不能計算相對表現。"
            continue
        spy_pct = (float(after)/float(before)-1)*100
        result.at[idx, "spy_baseline_close"] = float(before)
        result.at[idx, "spy_reaction_close"] = float(after)
        result.at[idx, "spy_close_to_close_pct"] = spy_pct
        result.at[idx, "relative_to_spy_pp"] = float(stock_pct) - spy_pct
        result.at[idx, "market_context_status"] = "有相同交易日"
        result.at[idx, "market_context_note"] = (
            "個股漲跌幅減去同期 SPY 漲跌幅，單位為百分點；"
            "只是相對表現，不是風險調整超額報酬或財報造成的影響。"
        )
    return result


def market_context_commentary(event):
    """Plain Chinese explanation, never claiming causal attribution."""
    if event.get("market_context_status") != "有相同交易日":
        return "目前無法與 SPY 可靠比較："+str(event.get("market_context_note","缺少行情。"))
    stock = float(event["close_to_close_pct"])
    spy = float(event["spy_close_to_close_pct"])
    difference = float(event["relative_to_spy_pp"])
    direction = "領先" if difference>0 else "落後" if difference<0 else "相同"
    return (
        f"相同交易日區間內：個股 {stock:+.2f}%、SPY {spy:+.2f}%；"
        f"個股相對 SPY {direction} {abs(difference):.2f} 個百分點。"
        "這只是收盤價相對變化，非風險調整後的異常報酬，"
        "不能證明由財報或特定新聞造成，也未計入股利與交易成本。"
    )
