"""Auditable, best-effort US equity fundamentals from Yahoo Finance via yfinance.

Separate fiscal quarter-end statement data from earnings-announcement EPS consensus.
No invented guidance or revenue analyst estimates. Provider availability can vary.
"""
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

ALLOWED_US_STOCKS = ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA")
SOURCE_NAME = "Yahoo Finance（經 yfinance 取得，非企業原始公告）"
STATEMENT_ALIASES = {
    "revenue": ("Total Revenue", "Operating Revenue"),
    "gross_profit": ("Gross Profit",),
    "operating_income": ("Operating Income",),
    "net_income": ("Net Income", "Net Income Common Stockholders"),
    "statement_eps": ("Diluted EPS", "Basic EPS"),
}


def _number(value):
    """Return a finite float or None; never convert unavailable data to zero."""
    try:
        if pd.isna(value):
            return None
        result = float(value)
        if not pd.notna(result) or abs(result) == float("inf"):
            return None
        return result
    except (TypeError, ValueError, OverflowError):
        return None


def _statement_number(series, names):
    for key in names:
        if key in series.index:
            number = _number(series[key])
            if number is not None:
                return number
    return None


def _date(value):
    try:
        stamp = pd.Timestamp(value)
        if pd.isna(stamp):
            return None
        return stamp.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def extract_quarterly_income(frame, max_quarters=8, as_of=None):
    """Normalize quarterly statement columns into chronological observation rows."""
    columns = ["period_end", "revenue", "gross_profit", "gross_margin_pct",
               "operating_income", "net_income", "statement_eps", "revenue_yoy_pct"]
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(columns=columns)
    cutoff = pd.Timestamp.now(tz="UTC") if as_of is None else pd.Timestamp(as_of)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    observations = []
    seen = set()
    for column in frame.columns:
        period = _date(column)
        if period is None or period in seen or pd.Timestamp(period).tz_localize("UTC") > cutoff:
            # Financial statement future-dated columns must never count as announced results.
            continue
        seen.add(period)
        values = frame[column]
        if not isinstance(values, pd.Series):
            continue
        row = {"period_end": period}
        for field, aliases in STATEMENT_ALIASES.items():
            row[field] = _statement_number(values, aliases)
        gross, revenue = row["gross_profit"], row["revenue"]
        row["gross_margin_pct"] = gross / revenue * 100 if gross is not None and revenue and revenue > 0 else None
        row["revenue_yoy_pct"] = None
        observations.append(row)
    observations.sort(key=lambda item: item["period_end"], reverse=True)
    # Include extra history to calculate year-over-year before trimming.
    for row in observations:
        current = pd.Timestamp(row["period_end"])
        target = current - pd.DateOffset(years=1)
        prior = next((
            other for other in observations
            if other is not row and abs((pd.Timestamp(other["period_end"]) - target).days) <= 14
        ), None)
        if prior and row["revenue"] is not None and prior["revenue"] is not None and prior["revenue"] > 0:
            row["revenue_yoy_pct"] = (row["revenue"] / prior["revenue"] - 1) * 100
    return pd.DataFrame(observations[:max_quarters], columns=columns)


def extract_eps_consensus(frame, max_events=12, as_of=None):
    """Separate earnings-announcement EPS actual/estimate pairs from GAAP diluted EPS.

    Dates reflect the provider's earnings calendar, not the fiscal quarter end.
    Do not join these observations with fiscal rows without authoritative matching.
    """
    columns = ["announcement_date", "eps_estimate", "eps_reported", "eps_surprise_pct", "state"]
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(columns=columns)
    current = pd.Timestamp.now(tz="UTC") if as_of is None else pd.Timestamp(as_of)
    current = current.tz_localize("UTC") if current.tzinfo is None else current.tz_convert("UTC")
    observations = []
    seen = set()
    for index, row in frame.iterrows():
        try:
            when = pd.Timestamp(index)
            if pd.isna(when):
                continue
            # Important: never invent a UTC timezone for a naive Yahoo timestamp.
            # Keep it naive, so the downstream US price-event matcher refuses
            # to assign a premarket/afterhours reaction without a real zone.
            unknown_timezone = when.tzinfo is None
            if not unknown_timezone:
                when = when.tz_convert("UTC")
        except (TypeError, ValueError, OverflowError):
            continue
        # The calendar can contain duplicate event rows (call, announcement).
        day = when.date().isoformat()
        if day in seen:
            continue
        seen.add(day)
        estimate = _number(row.get("EPS Estimate"))
        reported = _number(row.get("Reported EPS"))
        # Do not call future/pending EPS a reported result. Unknown-timezone
        # announcements dated today are conservatively treated as pending.
        if (when.date() >= current.date() if unknown_timezone else when > current):
            reported = None
        surprise = (reported - estimate) / abs(estimate) * 100 if (
            estimate is not None and reported is not None and estimate != 0
        ) else None
        state = "已公布（有預期可比）" if surprise is not None else ("已公布（無可比預期）" if reported is not None else "尚無已公布 EPS")
        observations.append({
            "announcement_date": when.isoformat(),
            "eps_estimate": estimate,
            "eps_reported": reported,
            "eps_surprise_pct": surprise,
            "state": state,
        })
    observations.sort(key=lambda item: item["announcement_date"], reverse=True)
    return pd.DataFrame(observations[:max_events], columns=columns)


def fetch_us_financials(symbol, ticker_factory=None, now=None):
    """Fetch each source independently, keeping partial results and missing-data notes.

    ticker_factory is injectable for deterministic offline tests.
    """
    symbol = str(symbol).upper().strip()
    if symbol not in ALLOWED_US_STOCKS:
        raise ValueError("目前只支援指定的美國上市公司，不包含 ETF、加密貨幣或台股。")
    ticker_factory = ticker_factory or yf.Ticker
    when = datetime.now(timezone.utc) if now is None else now
    result = {
        "symbol": symbol,
        "source": SOURCE_NAME,
        "retrieved_at": pd.Timestamp(when).isoformat(),
        "currency": None,
        "quarterly": extract_quarterly_income(None),
        "eps_events": extract_eps_consensus(None),
        "notes": [],
    }
    ticker = ticker_factory(symbol)
    try:
        result["quarterly"] = extract_quarterly_income(ticker.quarterly_income_stmt, as_of=when)
        if result["quarterly"].empty:
            result["notes"].append("季度損益表缺漏，不能推斷營收、獲利或毛利率。")
    except Exception:
        result["notes"].append("季度損益表無法取得；其餘資料仍可單獨顯示。")
    try:
        result["eps_events"] = extract_eps_consensus(ticker.get_earnings_dates(limit=12), as_of=when)
        if result["eps_events"].empty:
            result["notes"].append("Yahoo Finance 未提供可用的歷史 EPS 預期與實際值。")
    except Exception:
        result["notes"].append("EPS 預期與公布值資料無法取得；不得自行補入預期值。")
    try:
        metadata = ticker.info or {}
        currency = metadata.get("financialCurrency")
        if isinstance(currency, str) and len(currency)==3 and currency.isalpha():
            result["currency"] = currency.upper()
    except Exception:
        pass
    if result["currency"] is None:
        result["notes"].append("財報使用幣別無法由資料提供者核實；請查官方財報，勿假設一定為美元。")
    return result


def explain_report(report):
    """Chinese descriptions derived only from available numeric observations."""
    quarterly = report.get("quarterly")
    eps_events = report.get("eps_events")
    messages = []
    if isinstance(quarterly, pd.DataFrame) and not quarterly.empty:
        current = quarterly.iloc[0]
        revenue = _number(current.get("revenue"))
        if revenue is not None:
            messages.append("最近可得會計季度的營收數值已取得，但它不等於公司淨利。")
        growth = _number(current.get("revenue_yoy_pct"))
        if growth is not None:
            messages.append(f"相同會計季度的營收年增率約 {growth:+.1f}%；成長不等於股價必漲，仍要看獲利與市場預期。")
        else:
            messages.append("欠缺可比的去年同期資料，這一季無法可靠計算營收年增率。")
        margin = _number(current.get("gross_margin_pct"))
        if margin is not None:
            messages.append(f"最近一期毛利率約 {margin:.1f}%；它衡量產品或服務的毛利，不等於最終淨利率。")
        else:
            messages.append("缺少營收或毛利數據，不能計算毛利率。")
    else:
        messages.append("沒有可用的季度財務報表，本次不提供營收或獲利結論。")
    valid_eps = eps_events[
        eps_events["eps_surprise_pct"].notna()
    ] if isinstance(eps_events, pd.DataFrame) and not eps_events.empty else pd.DataFrame()
    if len(valid_eps):
        last = valid_eps.iloc[0]
        surprise = float(last["eps_surprise_pct"])
        when = str(last["announcement_date"])[:10]
        label = "高於" if surprise > 0 else "低於" if surprise < 0 else "符合"
        messages.append(f"{when} 的 EPS 公布值{label}供應商所列預估值，差距約 {surprise:+.1f}%；供應商未證明預估值是公告前的歷史快照，也不等於公告日股價漲跌。")
    else:
        messages.append("目前沒有可比的 EPS 實際值與市場預期值；不判斷是否超出預期。")
    messages.append("Yahoo Finance 的『Reported EPS』可能採用與損益表每股盈餘不同的調整口徑，兩者不可直接混用；供應商的 EPS Estimate 也未經公告前時間戳驗證。")
    messages.append("公司未來財測尚未從官方文件逐筆驗證，因此本頁不顯示推測的財測數字。")
    return messages
