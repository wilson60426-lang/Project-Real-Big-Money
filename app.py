import streamlit as st
import pandas as pd
from config.settings import EXCHANGE, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.sma_cross import generate_signals
from backtesting.engine import backtest

st.set_page_config(page_title="Project Real Big Money", page_icon="💰", layout="wide")
st.title("💰 Project Real Big Money")
st.caption("Crypto Research & Backtesting Terminal — research/paper trading only")

with st.sidebar:
    st.header("Backtest Settings")
    symbol = st.selectbox("Asset", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)
    limit = st.slider("Candles", 100, 1000, 500, 100)
    fee = st.number_input("Fee rate", min_value=0.0, max_value=0.01, value=float(FEE_RATE), step=0.0001, format="%.4f")
    run = st.button("Run Backtest", type="primary", use_container_width=True)

if run:
    with st.spinner("Fetching market data and running backtest..."):
        df = fetch_ohlcv(EXCHANGE, symbol, timeframe, limit)
        df = add_indicators(df)
        df = generate_signals(df)
        result = backtest(df, fee)

        clean = df.dropna().copy()
        clean["market_return"] = clean["close"].pct_change().fillna(0)
        clean["position"] = clean["signal"].shift(1).fillna(0)
        trades = clean["position"].diff().abs().fillna(0)
        clean["strategy_return"] = clean["position"] * clean["market_return"] - trades * fee
        clean["strategy_equity"] = (1 + clean["strategy_return"]).cumprod()
        clean["buy_hold_equity"] = (1 + clean["market_return"]).cumprod()
        buy_hold = float(clean["buy_hold_equity"].iloc[-1] - 1) if len(clean) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strategy Return", f"{result['total_return']:.2%}")
    c2.metric("Buy & Hold", f"{buy_hold:.2%}")
    c3.metric("Max Drawdown", f"{result['max_drawdown']:.2%}")
    c4.metric("Position Changes", result["trades"])

    st.subheader(f"{symbol} Price")
    st.line_chart(df.set_index("timestamp")[["close", "sma_20", "sma_50"]])

    st.subheader("Strategy vs Buy & Hold")
    st.line_chart(clean.set_index("timestamp")[["strategy_equity", "buy_hold_equity"]])

    st.subheader("RSI (14)")
    st.line_chart(df.set_index("timestamp")[["rsi_14"]])

    with st.expander("Latest market data"):
        st.dataframe(df.tail(100), use_container_width=True)
else:
    st.info("Choose settings on the left and click Run Backtest.")
    st.markdown("**v0.2:** BTC / ETH / SOL · SMA20/50 · RSI14 · fees · drawdown · Buy & Hold comparison")
