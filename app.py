import math
import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.history import fetch_history
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze
from backtesting.trade_engine import build_trades, trade_statistics
from backtesting.validation import regime_report, walk_forward, cost_stress, validation_score

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide")
st.title("💰 Project Real Big Money")
st.caption("v0.7｜Strategy Validation Engine｜目標不是找最好看的回測，而是找最難被證明是假的策略")

ZH={"SMA Cross":"均線交叉策略","RSI Reversion":"RSI 超賣反彈策略","Trend + RSI":"趨勢＋RSI 策略"}
with st.sidebar:
    st.header("⚙️ 驗證設定")
    mode=st.radio("介面",["🌱 新手模式","🔬 專業模式"])
    symbol=st.selectbox("幣種",["BTC/USDT","ETH/USDT","SOL/USDT"])
    timeframe=st.selectbox("K線週期",["1h","4h","1d"],index=0)
    years=st.select_slider("歷史資料",options=[1,2,3,5],value=3,format_func=lambda x:f"{x} 年")
    strategy=st.selectbox("策略",list(STRATEGIES),format_func=lambda x:ZH[x])
    fee=st.number_input("單邊手續費",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f")
    slip=st.number_input("單邊滑價",0.0,0.01,0.0005,0.0001,format="%.4f")
    run=st.button("🧪 開始策略驗證",type="primary",use_container_width=True)

with st.expander("🎓 新手：v0.7 在檢查什麼？"):
    st.markdown("""不是只問「以前賺多少」，而是故意讓策略接受更難的考試：

**長時間資料** → **完整交易樣本** → **牛熊盤整** → **Walk-Forward 未知資料** → **成本/滑價惡化測試**。

PASS 也不是「可以直接買」，只是代表這套策略值得進下一階段研究。""")

if not run:
    st.info("👈 選好條件後按「開始策略驗證」。第一次建議 BTC / 1h / 3年。下載多年資料第一次可能需要一些時間。")
    st.stop()

with st.spinner("正在下載多年歷史資料並進行多層驗證，第一次可能較久…"):
    raw=fetch_history(EXCHANGE,symbol,timeframe,years)
    base=add_indicators(raw)
    sig=STRATEGIES[strategy](base)
    equity,m=analyze(sig,fee,timeframe)
    trades=build_trades(sig,fee,slip); ts=trade_statistics(trades)
    regimes=regime_report(sig,fee,timeframe)
    wf=walk_forward(sig,fee,timeframe,5)
    stress=cost_stress(sig,fee,timeframe,slip)
    score,status,reasons=validation_score(years,ts,wf,regimes,stress)

icon={"PASS":"🟢","WATCH":"🟡","FAIL":"🔴"}[status]
st.success(f"完成｜{symbol}｜{ZH[strategy]}｜{years}年｜{len(raw):,} 根 K 線")

if mode=="🌱 新手模式":
    st.header(f"{icon} 策略驗證：{score}/100｜{status}")
    st.progress(score/100)
    st.caption("這不是賺錢機率。它代表策略目前通過多少項研究檢查。")
    a,b,c,d=st.columns(4)
    a.metric("歷史跨度",f"{years} 年")
    b.metric("完整交易",f"{ts['trades']} 筆")
    c.metric("逐筆勝率",f"{ts['win_rate']:.1%}")
    d.metric("每筆期望值",f"{ts['expectancy']:.2%}")
    st.subheader("🧪 五道考試")
    wf_rate=float(wf["PASS"].mean()) if len(wf) else 0
    tests=[
      ("歷史資料","PASS" if years>=3 else "WATCH",f"目前使用 {years} 年資料"),
      ("交易樣本","PASS" if ts["trades"]>=100 else "WATCH" if ts["trades"]>=30 else "FAIL",f"{ts['trades']} 筆完整交易"),
      ("牛熊盤整","PASS" if len(regimes)>=3 and (regimes["報酬"]>0).sum()>=2 else "WATCH",f"測到 {len(regimes)} 種市場環境"),
      ("Walk-Forward","PASS" if wf_rate>=.6 else "WATCH" if wf_rate>=.4 else "FAIL",f"{wf['PASS'].sum() if len(wf) else 0}/{len(wf)} 個未知區段通過"),
      ("成本壓力","PASS" if len(stress) and stress.iloc[-1]["Expectancy"]>0 else "FAIL","交易成本提高到 3 倍後再次檢查")
    ]
    for n,s,desc in tests:
        ic={"PASS":"🟢","WATCH":"🟡","FAIL":"🔴"}[s]
        st.write(f"{ic} **{n}｜{s}** — {desc}")
    if reasons:
        st.subheader("⚠️ 系統目前最擔心")
        for r in reasons: st.warning(r)
    st.subheader("🚦 我現在該怎麼做？")
    if status=="PASS": st.success("值得繼續研究與 Paper Trading；仍不代表適合投入真實資金。")
    elif status=="WATCH": st.warning("有一些證據，但仍有弱點。先處理黃色項目，不建議進入實盤。")
    else: st.error("目前驗證不足。與其調參數把結果修漂亮，更建議先淘汰或重新思考策略。")
else:
    st.header("🔬 專業驗證中心")
    c=st.columns(6)
    for col,(n,v) in zip(c,[("Score",score),("Return",f"{m['total_return']:.2%}"),("Max DD",f"{m['max_drawdown']:.2%}"),
                              ("Trades",ts["trades"]),("Expectancy",f"{ts['expectancy']:.3%}"),("Win Rate",f"{ts['win_rate']:.1%}")]):
        col.metric(n,v)
    st.subheader("市場環境")
    st.dataframe(regimes,use_container_width=True)
    st.subheader("Walk-Forward")
    st.dataframe(wf,use_container_width=True)
    st.subheader("成本 / 滑價壓力測試")
    st.dataframe(stress,use_container_width=True)
    st.subheader("策略淨值 vs Buy & Hold")
    st.line_chart(equity.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
    with st.expander("逐筆交易"):
        st.dataframe(trades,use_container_width=True)

st.divider()
st.caption("v0.7｜PASS ≠ 買入訊號。驗證分數是研究輔助工具，不是未來獲利機率。下一階段仍應加入參數穩健性、Monte Carlo 與更嚴格的統計檢定。")
