import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from indicators.basic import add_indicators

def describe_indicators(df):
    d=add_indicators(df)
    messages=[]
    if len(d)<50:
        messages.append("資料不足 50 根 K 線：長期均線尚未完整形成，趨勢判讀應保留。")
        return d,messages
    last=d.iloc[-1]
    if pd.notna(last["sma_20"]) and pd.notna(last["sma_50"]):
        if last["sma_20"]>last["sma_50"]:
            messages.append("SMA20 高於 SMA50：短期平均價格較強，但均線來自同一批價格，不能視為兩個獨立證據。")
        else:
            messages.append("SMA20 不高於 SMA50：短期平均價格較弱；不代表價格必然繼續下跌。")
    rsi=last["rsi_14"]
    if pd.notna(rsi):
        if rsi>=70: messages.append("RSI ≥70：近期上漲動能較強，可能偏熱；不代表立即反轉。")
        elif rsi<=30: messages.append("RSI ≤30：近期下跌動能較強，可能偏冷；不代表已經落底。")
        else: messages.append("RSI 在 30～70：沒有進入常用極端區，不能單靠 RSI 決定方向。")
    if pd.notna(last["macd_hist"]) and len(d)>1 and pd.notna(d["macd_hist"].iloc[-2]):
        previous=d["macd_hist"].iloc[-2]
        current=last["macd_hist"]
        if current>previous: messages.append("MACD 柱狀體較前一根上升：短期動能正在改善；若仍為負值，僅表示下跌動能可能減弱。")
        else: messages.append("MACD 柱狀體較前一根下降：短期動能正在轉弱；不能單獨預測後續漲跌。")
    if pd.notna(last["bb_upper"]) and pd.notna(last["bb_lower"]):
        if last["close"]>last["bb_upper"]: messages.append("價格高於布林上軌：相對近期波動區間偏高；強勢行情也可能持續沿上軌運行。")
        elif last["close"]<last["bb_lower"]: messages.append("價格低於布林下軌：相對近期波動區間偏低；不保證反彈。")
        else: messages.append("價格在布林通道內：目前仍處於近期統計波動區間。")
    if pd.notna(last["atr_14"]) and last["close"]>0:
        messages.append(f"ATR14 約為價格的 {last['atr_14']/last['close']:.2%}：代表近期每根 K 線的平均真實波動幅度，不表示上漲或下跌方向。")
    messages.append("以上指標多數由同一組價格計算，彼此相關；多個指標同向不等於多份獨立證據。")
    return d,messages

def make_chart(df,symbol):
    d,messages=describe_indicators(df)
    fig=make_subplots(rows=4,cols=1,shared_xaxes=True,vertical_spacing=0.035,row_heights=[0.57,0.13,0.15,0.15])
    fig.add_trace(go.Candlestick(x=d["timestamp"],open=d["open"],high=d["high"],low=d["low"],close=d["close"],name="K 線"),row=1,col=1)
    for name,color in [("sma_20","#e6a23c"),("sma_50","#508ee6"),("ema_12","#20a787"),("bb_upper","#999999"),("bb_lower","#999999")]:
        fig.add_trace(go.Scatter(x=d["timestamp"],y=d[name],mode="lines",name=name.upper(),line=dict(color=color,width=1 if name.startswith("bb_") else 1.6,dash="dot" if name.startswith("bb_") else "solid")),row=1,col=1)
    fig.add_trace(go.Bar(x=d["timestamp"],y=d["volume"],name="成交量",marker_color="#7b8794"),row=2,col=1)
    fig.add_trace(go.Scatter(x=d["timestamp"],y=d["rsi_14"],name="RSI 14",line=dict(color="#a77de3")),row=3,col=1)
    fig.add_hline(y=70,row=3,col=1,line_dash="dot",line_color="#d76565")
    fig.add_hline(y=30,row=3,col=1,line_dash="dot",line_color="#3ba785")
    fig.add_trace(go.Bar(x=d["timestamp"],y=d["macd_hist"],name="MACD 柱",marker_color="#8f9eb3"),row=4,col=1)
    fig.add_trace(go.Scatter(x=d["timestamp"],y=d["macd"],name="MACD",line=dict(color="#e6a23c")),row=4,col=1)
    fig.add_trace(go.Scatter(x=d["timestamp"],y=d["macd_signal"],name="MACD 訊號線",line=dict(color="#508ee6")),row=4,col=1)
    fig.update_layout(title=symbol+"｜智慧 K 線與指標",height=880,xaxis_rangeslider_visible=False,hovermode="x unified",legend=dict(orientation="h",y=1.06,x=0))
    for row,title in [(1,"價格"),(2,"成交量"),(3,"RSI"),(4,"MACD")]:
        fig.update_yaxes(title_text=title,row=row,col=1)
    fig.update_yaxes(range=[0,100],row=3,col=1)
    return fig,messages
