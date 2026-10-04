import math
import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze, split_validation

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide")
st.title("💰 Project Real Big Money")
st.caption("v0.4｜加密貨幣策略研究工具｜目前僅供研究與模擬，不會自動下單")

STRATEGY_ZH={
    "SMA Cross":"均線交叉策略",
    "RSI Reversion":"RSI 超賣反彈策略",
    "Trend + RSI":"趨勢＋RSI 策略",
}
STRATEGY_HELP={
    "SMA Cross":"短期均線高於長期均線時偏多，反之偏空。",
    "RSI Reversion":"RSI 低於 30 時視為超賣，測試反彈機會。",
    "Trend + RSI":"同時參考均線方向與 RSI 強弱，條件較嚴格。",
}

with st.sidebar:
    st.header("⚙️ 回測設定")
    symbol=st.selectbox("選擇幣種",["BTC/USDT","ETH/USDT","SOL/USDT"],help="目前先提供 BTC、ETH、SOL。")
    timeframe=st.selectbox("K 線週期",["15m","1h","4h","1d"],index=1,help="1h = 每根 K 線代表 1 小時。")
    strategy_name=st.selectbox("選擇策略",list(STRATEGIES),format_func=lambda x: STRATEGY_ZH[x])
    st.caption("📘 "+STRATEGY_HELP[strategy_name])
    limit=st.slider("分析 K 線數量",200,1000,500,100,help="數量越多，涵蓋的歷史時間越長。")
    fee=st.number_input("單次交易成本",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f",help="0.001 = 0.1%。回測會把交易成本算進去。")
    validate=st.checkbox("啟用 70/30 樣本外驗證",value=True,help="前 70% 資料用來觀察策略，後 30% 用來檢查策略是否仍有效。")
    run=st.button("▶ 開始分析",type="primary",use_container_width=True)

with st.expander("📖 第一次使用？先看這裡",expanded=False):
    st.markdown("""
**你不需要先懂所有量化名詞。**

1. 選幣種，例如 BTC。
2. K 線週期先用 **1h**。
3. 選一個策略。
4. 其他設定先維持預設值。
5. 按 **開始分析**。
6. 先看「策略健檢」，再看詳細數字。

**重要：** 回測賺錢不代表未來一定賺錢。本工具目前不會送出真實交易訂單。
""")

if not run:
    st.info("👈 第一次使用可先保持預設值，直接按左側「開始分析」。")
    st.subheader("你會看到什麼？")
    a,b,c=st.columns(3)
    a.markdown("### ① 有沒有賺？\n比較策略報酬與單純持有。")
    b.markdown("### ② 風險多大？\n看最大回撤與風險調整後績效。")
    c.markdown("### ③ 是否可靠？\n用後 30% 資料再次驗證。")
    st.stop()

with st.spinner("正在取得市場資料並進行分析…"):
    raw=fetch_ohlcv(EXCHANGE,symbol,timeframe,limit)
    base=add_indicators(raw)
    df=STRATEGIES[strategy_name](base)
    results,metrics=analyze(df,fee,timeframe)

st.success(f"分析完成：{symbol}｜{STRATEGY_ZH[strategy_name]}｜{timeframe}")

ret=metrics["total_return"]; bh=metrics["buy_hold"]; dd=metrics["max_drawdown"]
sh=metrics["sharpe"]; pf=metrics["profit_factor"]

st.subheader("🩺 策略健檢")
if ret>0 and ret>bh and sh>1:
    st.success("🟢 初步表現不錯：這段歷史資料中策略為正報酬、優於單純持有，而且 Sharpe > 1。仍需查看樣本外驗證。")
elif ret>0:
    st.warning("🟡 有正報酬，但不代表策略具有穩定優勢。請比較 Buy & Hold、回撤與樣本外結果。")
else:
    st.error("🔴 這段歷史資料中策略為負報酬。目前不適合因為這次回測就拿去實盤。")

c1,c2,c3,c4=st.columns(4)
c1.metric("策略報酬",f"{ret:.2%}",help="依目前策略與交易成本計算的歷史報酬。")
c2.metric("單純持有報酬",f"{bh:.2%}",help="同一期間買入後不交易的報酬。")
c3.metric("最大回撤",f"{dd:.2%}",help="歷史上從高點到低點最大的跌幅。越接近 0 通常越好。")
c4.metric("Sharpe 夏普比率",f"{sh:.2f}",help="衡量承擔波動後取得的報酬。通常越高越好，但不能單獨判斷策略。")

with st.expander("🔬 查看進階指標"):
    a,b,c,d=st.columns(4)
    a.metric("Sortino 索提諾比率",f"{metrics['sortino']:.2f}",help="類似 Sharpe，但更聚焦下跌波動。")
    b.metric("勝率",f"{metrics['win_rate']:.1%}",help="目前計算方式為持倉期間正報酬 K 線的比例，不等同完整逐筆交易勝率。")
    pf_text="∞" if math.isinf(pf) else f"{pf:.2f}"
    c.metric("Profit Factor 獲利因子",pf_text,help="總正報酬 ÷ 總負報酬。大於 1 代表這段資料中正報酬總量較高。")
    d.metric("部位變動次數",metrics["position_changes"],help="策略部位改變的次數，不一定等同完整交易筆數。")

st.subheader("📈 策略 vs 單純持有")
st.caption("起點都設為 1。線越高代表累積績效越高。")
st.line_chart(results.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])

st.subheader("💹 價格與均線")
st.caption("Close = 收盤價；SMA20 = 20 期均線；SMA50 = 50 期均線。")
st.line_chart(base.set_index("timestamp")[["close","sma_20","sma_50"]])

st.subheader("🌡️ RSI 相對強弱指標")
st.caption("一般常把 RSI < 30 視為偏超賣、RSI > 70 視為偏超買，但不能單獨作為買賣依據。")
st.line_chart(base.set_index("timestamp")[["rsi_14"]])

if validate:
    _,train_m,test,test_m=split_validation(df,fee,timeframe)
    st.subheader("🧪 70/30 樣本外驗證")
    st.caption("前 70% 與後 30% 分開看。後 30% 可用來檢查策略是否只是在前段資料看起來有效。")
    a,b,c,d=st.columns(4)
    a.metric("前 70% 報酬",f"{train_m['total_return']:.2%}")
    b.metric("後 30% 報酬",f"{test_m['total_return']:.2%}")
    c.metric("後 30% Sharpe",f"{test_m['sharpe']:.2f}")
    d.metric("後 30% 最大回撤",f"{test_m['max_drawdown']:.2%}")
    if train_m["total_return"]>0 and test_m["total_return"]<0:
        st.error("⚠️ 過度擬合警訊：前段賺錢，但後段資料轉為虧損。不要只看漂亮的歷史績效。")
    elif test_m["total_return"]>0 and test_m["sharpe"]>0:
        st.success("✅ 後段資料仍為正報酬，但仍需要更長歷史、不同市場週期與更多穩健性測試。")
    else:
        st.warning("⚠️ 樣本外結果沒有顯示明顯優勢，建議調整或淘汰此策略。")

with st.expander("📋 查看原始回測明細"):
    show=results[["timestamp","close","signal","position","market_return","strategy_return","strategy_equity"]].tail(200)
    show=show.rename(columns={"timestamp":"時間","close":"收盤價","signal":"策略訊號","position":"持倉方向","market_return":"市場報酬","strategy_return":"策略報酬","strategy_equity":"策略淨值"})
    st.dataframe(show,use_container_width=True)

st.divider()
st.caption("⚠️ 本工具為研究用途，不構成投資建議。v0.4 沒有真實下單功能。")
