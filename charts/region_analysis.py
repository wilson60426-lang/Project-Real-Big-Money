"""Explain a user-selected consecutive candle window without forecasting."""
import pandas as pd
from indicators.basic import add_indicators
from indicators.twin_range import twin_range_filter

def explain_region(df,start,end):
    d=df.copy().sort_values("timestamp").reset_index(drop=True)
    if start>end: start,end=end,start
    if start<0 or end>=len(d) or end-start<2:
        raise ValueError("請至少選取連續 3 根 K 線。")
    full=twin_range_filter(add_indicators(d))
    x=full.iloc[start:end+1]
    first,last=x.iloc[0],x.iloc[-1]
    base=float(first["open"])
    change=float(last["close"])/base-1 if base>0 else float("nan")
    high=float(x["high"].max());low=float(x["low"].min())
    span=(high-low)/base if base>0 else float("nan")
    messages=[
        f"這段共 {len(x)} 根 K 線，從第一根開盤到最後一根收盤，變動 {change:+.2%}。",
        f"區間最高 {high:,.4f}、最低 {low:,.4f}；高低價差約為起始價格的 {span:.2%}。",
    ]
    if len(x)>=10 and x["volume"].notna().any():
        half=len(x)//2
        early=x["volume"].iloc[:half].mean()
        late=x["volume"].iloc[half:].mean()
        if pd.notna(early) and early>0 and pd.notna(late):
            messages.append(f"後半段平均成交量相對前半段變化 {late/early-1:+.1%}；量增不必然代表上漲。")
    if pd.notna(last["rsi_14"]):
        messages.append(f"區間末端 RSI14 為 {last['rsi_14']:.1f}；偏高或偏低都不能單獨確認反轉。")
    if pd.notna(last["trf_filter"]):
        label="偏多觀察" if last["trf_long_setup"] else "偏空觀察" if last["trf_short_setup"] else "方向尚不明確"
        messages.append(f"區間末端 Twin Range Filter 顯示「{label}」，濾波線約 {last['trf_filter']:,.4f}；盤整時可能反覆切換。")
    messages.append("以上僅描述所選歷史區段；未檢查新聞因果，也不能據此預測下一根 K 線。")
    return messages
