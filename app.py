import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze, split_validation

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide")
st.title("💰 Project Real Big Money")
st.caption("v0.3 · Crypto strategy research & validation terminal · no live execution")

with st.sidebar:
    st.header("Research Settings")
    symbol=st.selectbox("Asset",["BTC/USDT","ETH/USDT","SOL/USDT"])
    timeframe=st.selectbox("Timeframe",["15m","1h","4h","1d"],index=1)
    strategy_name=st.selectbox("Strategy",list(STRATEGIES))
    limit=st.slider("Candles",200,1000,500,100)
    fee=st.number_input("Fee rate",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f")
    validate=st.checkbox("70/30 Out-of-Sample validation",value=True)
    run=st.button("Run Research",type="primary",use_container_width=True)

if not run:
    st.info("Choose settings and click Run Research.")
    st.markdown("**v0.3:** multiple strategies · Sharpe · Sortino · Profit Factor · win rate · Buy & Hold · 70/30 validation")
    st.stop()

with st.spinner("Fetching market data and evaluating strategy..."):
    raw=fetch_ohlcv(EXCHANGE,symbol,timeframe,limit)
    base=add_indicators(raw)
    df=STRATEGIES[strategy_name](base)
    results,metrics=analyze(df,fee,timeframe)

cols=st.columns(7)
labels=[("Return","total_return",".2%"),("Buy & Hold","buy_hold",".2%"),("Max DD","max_drawdown",".2%"),
        ("Sharpe","sharpe",".2f"),("Sortino","sortino",".2f"),("Win Rate","win_rate",".1%"),
        ("Profit Factor","profit_factor",".2f")]
for c,(label,key,fmt) in zip(cols,labels):
    c.metric(label,format(metrics[key],fmt))

st.subheader(f"{symbol} · {strategy_name}")
st.line_chart(base.set_index("timestamp")[["close","sma_20","sma_50"]])
st.subheader("Strategy vs Buy & Hold")
st.line_chart(results.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
st.subheader("RSI (14)")
st.line_chart(base.set_index("timestamp")[["rsi_14"]])

if validate:
    _,train_m,test,test_m=split_validation(df,fee,timeframe)
    st.subheader("70/30 Out-of-Sample Check")
    a,b,c,d=st.columns(4)
    a.metric("Train Return",f"{train_m['total_return']:.2%}")
    b.metric("Test Return",f"{test_m['total_return']:.2%}")
    c.metric("Test Sharpe",f"{test_m['sharpe']:.2f}")
    d.metric("Test Max DD",f"{test_m['max_drawdown']:.2%}")
    if train_m["total_return"]>0 and test_m["total_return"]<0:
        st.warning("The strategy was profitable in-sample but lost money out-of-sample. Treat this as an overfitting warning.")

st.subheader("Position / return detail")
show=results[["timestamp","close","signal","position","market_return","strategy_return","strategy_equity"]].tail(200)
st.dataframe(show,use_container_width=True)
st.caption("Research output is not investment advice. v0.3 intentionally has no live-order execution.")
