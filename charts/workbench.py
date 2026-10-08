import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from indicators.basic import add_indicators

def describe_indicators(df):
    d=add_indicators(df)
    if len(d)<50:
        return d,["資料少於 50 根 K 線，長期均線可能尚未形成，暫時不要解讀趨勢。"]
    last=d.iloc[-1]; messages=[]
    if pd.notna(last["sma_20"]) and pd.notna(last["sma_50"]):
        if last["sma_20"]>last["sma_50"]:
            messages.append("短期 20 根均價高於 50 根均價：近期價格平均位置較強，但不保證繼續上漲。")
        else:
            messages.append("短期 20 根均價低於或等於 50 根均價：近期價格平均位置偏弱，仍可能反彈。")
    rsi=last["rsi_14"]
    if pd.notna(rsi):
        if rsi>=70: messages.append("RSI 偏高：近期上漲動能較強，留意追價風險；不代表馬上會跌。")
        elif rsi<=30: messages.append("RSI 偏低：近期下跌動能較強，不代表已經落底。")
        else: messages.append("RSI 在 30～70 之間：沒有達到常見的極端區間，仍需搭配趨勢判斷。")
    return d,messages

def make_chart(df,symbol):
    d,messages=describe_indicators(df)
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.035,row_heights=[0.65,0.15,0.20])
    fig.add_trace(go.Candlestick(x=d["timestamp"],open=d["open"],high=d["high"],low=d["low"],close=d["close"],name="K 線"),row=1,col=1)
    for name,color in [("sma_20","#e6a23c"),("sma_50","#508ee6")]:
        fig.add_trace(go.Scatter(x=d["timestamp"],y=d[name],mode="lines",name=name.upper(),line=dict(color=color,width=1.5)),row=1,col=1)
    fig.add_trace(go.Bar(x=d["timestamp"],y=d["volume"],name="成交量",marker_color="#7b8794"),row=2,col=1)
    fig.add_trace(go.Scatter(x=d["timestamp"],y=d["rsi_14"],name="RSI 14",line=dict(color="#a77de3")),row=3,col=1)
    fig.add_hline(y=70,row=3,col=1,line_dash="dot",line_color="#d76565")
    fig.add_hline(y=30,row=3,col=1,line_dash="dot",line_color="#3ba785")
    fig.update_layout(title=symbol+"｜K 線與指標",height=720,xaxis_rangeslider_visible=False,hovermode="x unified",legend=dict(orientation="h",y=1.04,x=0))
    fig.update_yaxes(title_text="價格",row=1,col=1)
    fig.update_yaxes(title_text="成交量",row=2,col=1)
    fig.update_yaxes(title_text="RSI",range=[0,100],row=3,col=1)
    return fig,messages
