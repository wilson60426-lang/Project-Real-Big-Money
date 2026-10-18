"""Conservative US earnings-release / daily-candle alignment.

Uses the provider's EPS release timestamps, never fiscal-quarter end dates.
Regular US equity session: 09:30--16:00 America/New_York. No claim of causality.
Unsupported intraday timing, unknown timezone and unfinished daily bars => no return.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from data.fundamentals import ALLOWED_US_STOCKS

NEW_YORK = ZoneInfo("America/New_York")
RESULT_COLUMNS = [
    "announcement_date", "release_et", "timing", "baseline_date",
    "reaction_date", "baseline_close", "reaction_close",
    "close_to_close_pct", "status", "explanation",
]


def _now_utc(value=None):
    stamp = pd.Timestamp(datetime.now(timezone.utc) if value is None else value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def normalize_equity_prices(raw, now=None):
    """Return completed daily regular-session closes (unadjusted provider Close).

    Yahoo Finance's raw Close can still be restated for corporate actions. This is
    a descriptive price change, not dividend-adjusted total return.
    """
    columns = ["session_date", "timestamp", "open", "high", "low", "close", "volume"]
    if raw is None or not isinstance(raw, pd.DataFrame) or raw.empty:
        return pd.DataFrame(columns=columns)
    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if "Date" not in frame.columns and "Datetime" not in frame.columns and "timestamp" not in frame.columns:
        frame = frame.reset_index()
    frame.columns = [str(col).lower() for col in frame.columns]
    time_key = next((col for col in ("timestamp", "date", "datetime") if col in frame.columns), None)
    if not time_key or any(col not in frame.columns for col in ("open", "high", "low", "close")):
        return pd.DataFrame(columns=columns)
    dates = pd.to_datetime(frame[time_key], errors="coerce")
    if dates.dt.tz is not None:
        dates = dates.dt.tz_convert(NEW_YORK).dt.tz_localize(None)
    frame["session_date"] = dates.dt.date
    frame["timestamp"] = dates
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce") if col in frame.columns else 0
    frame = frame.dropna(subset=["session_date", "close", "open"])
    frame = frame.loc[(frame["close"] > 0) & (frame["open"] > 0)].copy()
    # Never publish a daily candle before the NY exchange session finishes with buffer.
    ny_now = _now_utc(now).tz_convert(NEW_YORK)
    today = ny_now.date()
    if (ny_now.hour, ny_now.minute) < (16, 30):
        frame = frame.loc[frame["session_date"] != today]
    frame = frame.loc[frame["session_date"] <= today]
    frame = frame.sort_values("session_date").drop_duplicates("session_date", keep="last")
    return frame[columns].reset_index(drop=True)


def fetch_us_daily_prices(symbol, ticker_factory=None, now=None):
    """Read free historical OHLC, with exact availability dependent on Yahoo."""
    ticker = str(symbol).strip().upper()
    if ticker not in ALLOWED_US_STOCKS:
        raise ValueError("只支援指定的美國上市公司，無法將 ETF 或加密貨幣當成美股財報。")
    factory = ticker_factory or yf.Ticker
    raw = factory(ticker).history(period="2y", interval="1d", auto_adjust=False, actions=False)
    return normalize_equity_prices(raw, now=now)


def _event_phase(stamp, available_dates):
    """An explicit timezone is mandatory for mapping to a US trading session."""
    if pd.isna(stamp):
        return "時間無效", None, None
    if stamp.tzinfo is None:
        return "發布時間缺少時區", None, None
    utc = stamp.tz_convert("UTC")
    # Midnight UTC commonly encodes a date-only field; no inferred session timing.
    if (utc.hour, utc.minute, utc.second) == (0, 0, 0):
        return "可能只有公告日期", None, None
    local = stamp.tz_convert(NEW_YORK)
    day = local.date()
    if day not in available_dates:
        # Weekends are definitely closed. Weekday gaps may be exchange holidays,
        # halts, or missing provider data: without a verified trading calendar
        # they must NOT be treated as a proven non-trading-day release.
        if day.weekday() >= 5:
            return "非交易日公布", local, day
        return "交易日資料缺漏／可能休市", local, day
    local_time = (local.hour, local.minute)
    if local_time < (9, 30):
        if local_time == (0, 0):
            return "可能只有公告日期", None, None
        return "盤前", local, day
    if local_time >= (16, 0):
        return "盤後", local, day
    return "盤中（無法用日 K 隔離事件影響）", local, day


def align_earnings_reactions(prices, events, now=None):
    """Find prior completed close and first completed close after release.

    A date within the trading session is not enough. Returns are suppressed
    when time is ambiguous, session data is sparse, or the response bar is open.
    """
    now_utc = _now_utc(now)
    result = []
    if not isinstance(events, pd.DataFrame) or events.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    clean = normalize_equity_prices(prices, now=now_utc)
    available_dates = set(clean["session_date"]) if not clean.empty else set()
    for _, event in events.iterrows():
        original = str(event.get("announcement_date", ""))
        row = {
            "announcement_date": original, "release_et": None, "timing": None,
            "baseline_date": None, "reaction_date": None, "baseline_close": None,
            "reaction_close": None, "close_to_close_pct": None, "status": "不可計算",
            "explanation": "",
        }
        try:
            stamp = pd.Timestamp(original)
            if pd.isna(stamp):
                raise ValueError("invalid date")
        except (ValueError, TypeError, OverflowError):
            row["explanation"] = "公告時間無效，無法比對 K 線。"
            result.append(row)
            continue
        if stamp.tzinfo is None:
            row["explanation"] = "資料來源沒有提供明確時區；不擅自把公告時間當作美東時間。"
            row["timing"] = "時間未確認"
            result.append(row)
            continue
        stamp_utc = stamp.tz_convert("UTC")
        if stamp_utc > now_utc or pd.isna(event.get("eps_reported")):
            row["explanation"] = "尚無已公布 EPS 或公告時間在未來；不計算市場反應。"
            row["timing"] = "未確認已公布"
            result.append(row)
            continue
        phase, local, day = _event_phase(stamp, available_dates)
        row["timing"] = phase
        if local is not None:
            row["release_et"] = local.isoformat()
        if day is None or phase.startswith(("可能", "盤中", "交易日資料缺漏")) or phase == "時間無效":
            row["explanation"] = "事件時點不足以用日 K 隔離行情反應，請核對公司正式公告時間或使用經授權的盤中資料。"
            result.append(row)
            continue
        if clean.empty:
            row["explanation"] = "沒有足夠的已收盤日 K 資料。"
            result.append(row)
            continue
        before = clean.loc[clean["session_date"] < day]
        after_date = clean.loc[clean["session_date"] > day]
        if phase == "盤前" and day in available_dates:
            baseline, reaction = before.tail(1), clean.loc[clean["session_date"] == day].head(1)
        elif phase == "盤後" and day in available_dates:
            baseline, reaction = clean.loc[clean["session_date"] == day].tail(1), after_date.head(1)
        else:
            baseline, reaction = before.tail(1), clean.loc[clean["session_date"] >= day].head(1)
        if baseline.empty or reaction.empty:
            row["explanation"] = "缺少公告前或公告後已完成交易日的收盤價。"
            result.append(row)
            continue
        first, second = baseline.iloc[0], reaction.iloc[0]
        # Refuse stale or sparse bars instead of fabricating a one-session return.
        lag_before = (day - first["session_date"]).days
        lag_after = (second["session_date"] - day).days
        if lag_before > 5 or lag_after > 5 or (second["session_date"] - first["session_date"]).days > 5:
            row["explanation"] = "交易日之間的資料間隔過大，無法可靠視為事件後首個收盤反應。"
            result.append(row)
            continue
        baseline_close, reaction_close = float(first["close"]), float(second["close"])
        if baseline_close <= 0:
            row["explanation"] = "公告前收盤價無效。"
            result.append(row)
            continue
        row.update({
            "baseline_date": first["session_date"].isoformat(),
            "reaction_date": second["session_date"].isoformat(),
            "baseline_close": baseline_close,
            "reaction_close": reaction_close,
            "close_to_close_pct": (reaction_close / baseline_close - 1) * 100,
            "status": "可觀察（非因果）",
            "explanation": "由公告前已完成收盤價比對到公告後首個完整交易日收盤價，包含盤外消息與其他共同因素；不是財報造成的報酬。",
        })
        result.append(row)
    return pd.DataFrame(result, columns=RESULT_COLUMNS)


def reaction_commentary(row):
    value = row.get("close_to_close_pct")
    if value is None or pd.isna(value):
        return "這筆公告沒有可可靠對應的日 K 反應。"+str(row.get("explanation", ""))
    tone = "上升" if value > 0 else "下降" if value < 0 else "持平"
    return (
        f"依供應商公告時間與完成的美股日 K，"
        f"從 {row['baseline_date']} 收盤至 {row['reaction_date']} 收盤，"
        f"價格{tone} {abs(float(value)):.2f}%。"
        "這是價格變化的時間對照，不能認定由財報或新聞造成；"
        "數值也不是含股利的總報酬。"
    )
