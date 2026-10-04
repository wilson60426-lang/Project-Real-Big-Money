import streamlit as st
from data.history import fetch_history
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.challenge import challenge_strategy

st.set_page_config(page_title="Strategy Challenge",page_icon="🔥",layout="wide")
st.title("🔥 Strategy Challenge")
st.caption("v0.9｜系統的工作不是稱讚策略，而是嘗試把它推翻。")
ZH={"SMA Cross":"均線交叉","RSI Reversion":"RSI 超賣反彈","Trend + RSI":"趨勢＋RSI"}
with st.sidebar:
    symbol=st.selectbox("Crypto",["BTC/USDT","ETH/USDT","SOL/USDT"])
    timeframe=st.selectbox("週期",["1h","4h","1d"])
    years=st.select_slider("歷史",options=[1,2,3,5],value=3,format_func=lambda x:f"{x}年")
    strategy=st.selectbox("策略",list(STRATEGIES),format_func=lambda x:ZH[x])
    fee=st.number_input("單邊手續費",value=.001,step=.0001,format="%.4f")
    slip=st.number_input("單邊滑價",value=.0005,step=.0001,format="%.4f")
    run=st.button("🔥 挑戰這個策略",type="primary",use_container_width=True)
if not run:
    st.info("按下按鈕後，系統會刻意尋找策略失效的地方。"); st.stop()
with st.spinner("正在反覆重抽樣、切年份、切市場環境並提高成本…"):
    raw=fetch_history("binance",symbol,timeframe,years)
    sig=STRATEGIES[strategy](add_indicators(raw))
    r=challenge_strategy(sig,fee,timeframe,slip)
icon={"PASS":"🟢","WATCH":"🟡","FAIL":"🔴"}[r["status"]]
st.header(f"{icon} Challenge Score：{r['score']}/100｜{r['status']}")
st.caption("不是獲利機率，而是策略目前撐過多少反證測試。")
st.dataframe(r["checks"],use_container_width=True,hide_index=True)
b=r["bootstrap"]; mc=r["monte_carlo"]
a,c,d=st.columns(3)
a.metric("Bootstrap 正期望比例",f"{b['positive_probability']:.1%}")
c.metric("期望值 90% 區間",f"{b['p05']:.2%} ～ {b['p95']:.2%}")
d.metric("Monte Carlo 壓力回撤",f"{mc['p95_worst_dd']:.1%}")
with st.expander("新手：這些數字是什麼？"):
    st.write("Bootstrap 反覆重抽歷史交易，檢查優勢是否只靠少數幸運交易。期望值區間若經常跨過 0，證據較弱。Monte Carlo 則觀察不同交易排列與抽樣下可能出現的更差資金路徑。")
tabs=st.tabs(["年份","市場環境","Walk-Forward","成本壓力"])
for tab,data in zip(tabs,[r["yearly"],r["regimes"],r["walk_forward"],r["stress"]]):
    with tab: st.dataframe(data,use_container_width=True,hide_index=True)
if r["status"]=="PASS": st.success("撐過目前多數挑戰。下一步仍是 Paper Trading，不是直接實盤。")
elif r["status"]=="WATCH": st.warning("存在明顯弱點，先處理 WATCH / FAIL。")
else: st.error("目前容易被反證。不要為了提高分數反覆調參數，否則可能過度擬合。")
st.caption("尚未加入 Deflated Sharpe、參數穩健性與策略搜尋次數追蹤。")
