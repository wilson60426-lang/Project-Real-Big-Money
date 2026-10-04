import math
import pandas as pd

def quality_score(metrics: dict, train_metrics: dict | None = None, test_metrics: dict | None = None, rows: int = 0) -> dict:
    parts = {}
    parts["資料量"] = min(20, max(0, rows / 1000 * 20))
    trades = metrics.get("position_changes", 0)
    parts["交易樣本"] = min(15, trades / 50 * 15)
    dd = abs(metrics.get("max_drawdown", 0))
    parts["風險控制"] = 15 if dd <= .15 else 10 if dd <= .30 else 4
    sh = metrics.get("sharpe", 0)
    parts["風險調整績效"] = 15 if sh >= 1.5 else 11 if sh >= 1 else 7 if sh > 0 else 2
    pf = metrics.get("profit_factor", 0)
    if math.isinf(pf): pf = 3
    parts["獲利品質"] = 15 if pf >= 1.5 else 10 if pf >= 1.1 else 4
    if train_metrics and test_metrics:
        tr, te = train_metrics.get("total_return",0), test_metrics.get("total_return",0)
        if te > 0 and test_metrics.get("sharpe",0) > 0:
            parts["樣本外驗證"] = 20
        elif tr > 0 and te < 0:
            parts["樣本外驗證"] = 3
        else:
            parts["樣本外驗證"] = 10
    else:
        parts["樣本外驗證"] = 5
    score = round(sum(parts.values()))
    if score >= 80: level, icon = "品質良好", "🟢"
    elif score >= 60: level, icon = "仍需驗證", "🟡"
    else: level, icon = "可信度不足", "🔴"
    return {"score": score, "level": level, "icon": icon, "parts": parts}

def beginner_verdict(metrics: dict, quality: dict) -> dict:
    ret=metrics.get("total_return",0); bh=metrics.get("buy_hold",0); dd=metrics.get("max_drawdown",0)
    profit = "有" if ret > 0 else "沒有"
    beats = ret - bh
    if quality["score"] >= 80 and ret > 0:
        action="值得繼續做模擬交易（Paper Trading），但不是實盤買入訊號。"
    elif quality["score"] >= 60:
        action="可以繼續研究，但目前證據還不足以進入真實交易。"
    else:
        action="先不要考慮實盤，應增加資料與改善策略後重新測試。"
    return {"profit":profit,"excess":beats,"drawdown":dd,"action":action}
