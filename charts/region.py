import pandas as pd
from indicators.basic import add_indicators
from indicators.twin_range import twin_range_filter

def explain_region(raw,indices,show_trf=True):
    d=raw.sort_values("timestamp").reset_index(drop=True)
    ids=sorted(set(int(i) for i in indices if 0<=int(i)<len(d)))
    if len(ids)<2: return ["至少選兩根 K 線才能分析區間。"]
    start,end=ids[0],ids[-1]
    x=d.iloc[start:end+1]
    first,last=float(x["close"].iloc[0]),float(x["close"].iloc[-1])
    if first<=0: return ["價格資料異常，無法計算漲跌幅。"]
    change=last/first-1
    high=float(x["high"].max()); low=float(x["low"].min())
    result=[f"選取 {len(x)} 根連續 K 線，從 {str(x['timestamp'].iloc[0])[:16]} 到 {str(x['timestamp'].iloc[-1])[:16]}。",
            f"收盤價由 {first:,.4f} 變為 {last:,.4f}，區間漲跌 {change:+.2%}；最高 {high:,.4f}，最低 {low:,.4f}。",
            "區間價格呈現上升" if change>0 else "區間價格呈現下降" if change<0 else "區間首尾收盤價相同"]
    if "volume" in x and x["volume"].notna().any():
        result.append(f"區間平均成交量 {x['volume'].mean():,.0f}；成交量是活動程度，不等於買盤或賣盤力量。")
    enriched=add_indicators(d)
    a,b=enriched.iloc[start],enriched.iloc[end]
    if pd.notna(a["rsi_14"]) and pd.notna(b["rsi_14"]):
        result.append(f"RSI 從 {a['rsi_14']:.1f} 變成 {b['rsi_14']:.1f}；這反映近期漲跌動能的變化，不保證反轉。")
    if show_trf:
        trf=twin_range_filter(d).iloc[end]
        if pd.notna(trf["trf_filter"]):
            trend="偏多" if trf["trf_long_setup"] else "偏空" if trf["trf_short_setup"] else "不明確"
            result.append(f"區間終點 Twin Range Filter 條件：{trend}；濾波線 {trf['trf_filter']:,.4f}。")
    result.append("這是所選歷史區間的描述，不是當時新聞的因果分析，也不是未來走勢預測。")
    return result
