"""Plot US earnings announcements against regular-session daily candles.

Markers indicate Yahoo Finance's reported announcement timestamps, not proof
of announcement content or its causal effect on price.
"""
import pandas as pd
import plotly.graph_objects as go

from analytics.earnings_reactions import normalize_equity_prices, NEW_YORK


def make_earnings_chart(prices, eps_events, symbol, max_bars=260):
    bars=normalize_equity_prices(prices)
    if bars.empty:
        return None, 0
    bars=bars.tail(max_bars).copy()
    fig=go.Figure()
    fig.add_trace(go.Candlestick(
        x=bars["session_date"],open=bars["open"],high=bars["high"],
        low=bars["low"],close=bars["close"],name="美股日 K（未還原 OHLC）",
        increasing_line_color="#18a886",decreasing_line_color="#d9676b",
    ))
    n_markers=0
    if isinstance(eps_events,pd.DataFrame) and not eps_events.empty:
        dates=set(bars["session_date"])
        for _,event in eps_events.iterrows():
            if pd.isna(event.get("eps_reported")):
                continue
            try:
                stamp=pd.Timestamp(event["announcement_date"])
                if pd.isna(stamp) or stamp.tzinfo is None:
                    continue
                et=stamp.tz_convert(NEW_YORK)
            except (TypeError,ValueError,OverflowError,KeyError):
                continue
            date=et.date()
            if date not in dates:
                # Do not mark an invented trading date or imply weekend trading.
                continue
            row=bars.loc[bars["session_date"]==date].iloc[0]
            fig.add_trace(go.Scatter(
                x=[date],y=[float(row["high"])*1.012],
                mode="markers",name="EPS 公告日（供應商日期）",
                marker=dict(symbol="diamond",size=11,color="#daa520"),
                customdata=[[et.strftime("%Y-%m-%d %H:%M %Z")]],
                hovertemplate="供應商 EPS 公告日期（美東）：%{customdata[0]}<extra></extra>",
                showlegend=n_markers==0,
            ))
            n_markers+=1
    fig.update_layout(
        title=symbol+"｜財報公告日期與美股日 K（非因果對照）",
        height=530,xaxis_title="美股交易日期（America/New_York）",
        yaxis_title="股票價格（Yahoo Finance 原幣）",
        xaxis_rangeslider_visible=False,hovermode="x unified",
        margin=dict(l=30,r=18,t=60,b=40),
        legend=dict(orientation="h",y=1.11),
    )
    return fig,n_markers
