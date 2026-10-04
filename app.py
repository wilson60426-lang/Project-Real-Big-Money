import math
import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze, split_validation
from backtesting.quality import quality_score, beginner_verdict
from backtesting.trade_engine import build_trades, trade_statistics

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide")
st.title("💰 Project Real Big Money")
st.caption("v0.6｜新手友善策略研究＋真正逐筆交易分析｜研究用途，不會自動下單")

ZH={"SMA Cross":"均線交叉策略","RSI Reversion":"RSI 超賣反彈策略","Trend + RSI":"趨勢＋RSI 策略"}
HELP={"SMA Cross":"比較短期與長期平均價格，觀察趨勢方向。",
"RSI Reversion":"尋找價格可能過度下跌後的反彈機會。",
"Trend + RSI":"同時參考趨勢與市場強弱，條件較嚴格。"}

with st.sidebar:
    st.header("⚙️ 回測設定")
    mode=st.radio("顯示模式",["🌱 新手模式","🔬 專業模式"])
    symbol=st.selectbox("我要研究哪個幣？",["BTC/USDT","ETH/USDT","SOL/USDT"])
    timeframe=st.selectbox("多久看一次價格？",["15m","1h","4h","1d"],index=1,help="1h = 每根 K 線代表一小時。")
    strategy=st.selectbox("使用哪個策略？",list(STRATEGIES),format_func=lambda x:ZH[x])
    st.caption("💡 "+HELP[strategy])
    limit=st.slider("歷史 K 線數量",200,1000,500,100)
    fee=st.number_input("單邊手續費率",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f",help="例如 0.001 = 0.1%。")
    slippage=st.number_input("單邊滑價假設",0.0,0.01,0.0005,0.0001,format="%.4f",help="滑價是理論價格與實際成交價格的落差。0.0005 = 0.05%。")
    run=st.button("▶ 開始回測",type="primary",use_container_width=True)

with st.expander("🎓 新手：這一版多了什麼？"):
    st.markdown("""
v0.6 開始把 **進場 → 持有 → 出場** 視為一筆完整交易。

所以「勝率」現在真的代表：**100 筆完整交易裡，有多少筆最後賺錢。**

同時加入滑價、平均賺賠、每筆期望值、最大連敗、MAE/MFE 等資料。
這仍然是歷史模擬，不代表未來結果。
""")

if not run:
    st.info("👈 第一次使用可以保持預設值，直接按「開始回測」。")
    st.markdown("### v0.6 會回答")
    a,b,c,d=st.columns(4)
    a.info("💰 **策略賺嗎？**\n\n看整體歷史績效。")
    b.info("🎯 **每筆交易如何？**\n\n真正逐筆統計。")
    c.info("🛡️ **風險多大？**\n\n回撤、連敗與 MAE。")
    d.info("🧪 **值得信嗎？**\n\n品質與樣本外驗證。")
    st.stop()

with st.spinner("正在取得資料並建立逐筆交易紀錄…"):
    raw=fetch_ohlcv(EXCHANGE,symbol,timeframe,limit)
    base=add_indicators(raw)
    signals=STRATEGIES[strategy](base)
    results,metrics=analyze(signals,fee,timeframe)
    _,train_m,test,test_m=split_validation(signals,fee,timeframe)
    quality=quality_score(metrics,train_m,test_m,len(results))
    verdict=beginner_verdict(metrics,quality)
    trades=build_trades(signals,fee,slippage)
    ts=trade_statistics(trades)

st.success(f"分析完成｜{symbol}｜{ZH[strategy]}｜{timeframe}")

if mode=="🌱 新手模式":
    st.header("📋 先看結論")
    st.markdown(f"## {quality['icon']} 回測品質：{quality['score']} / 100｜{quality['level']}")
    st.progress(quality["score"]/100)
    st.caption("品質分數不是賺錢機率，而是提醒你目前證據有多完整。")

    a,b,c=st.columns(3)
    a.metric("策略歷史報酬",f"{metrics['total_return']:.2%}")
    b.metric("真正逐筆勝率",f"{ts['win_rate']:.1%}",help="完整進場到出場後，最後淨報酬為正的交易比例。")
    c.metric("完整交易筆數",ts["trades"],help="樣本太少時，即使勝率很漂亮也不能太相信。")

    st.subheader("🎯 這套策略每次出手的品質如何？")
    x,y,z=st.columns(3)
    x.metric("平均賺一筆",f"{ts['avg_win']:.2%}")
    y.metric("平均賠一筆",f"{ts['avg_loss']:.2%}")
    z.metric("每筆期望值",f"{ts['expectancy']:.2%}",help="把所有完整交易平均後，一筆交易歷史上平均帶來多少淨報酬。")
    if ts["expectancy"]>0:
        st.success("🟢 歷史上每筆交易的平均結果為正。但仍要確認交易筆數是否足夠。")
    else:
        st.error("🔴 歷史上每筆交易的平均結果不是正值，目前沒有看到明顯交易優勢。")

    st.subheader("🛡️ 如果運氣不好，可能遇到什麼？")
    a,b,c=st.columns(3)
    a.metric("最大連續虧損",f"{ts['max_consecutive_losses']} 筆",help="歷史上最長連續虧損交易數。")
    b.metric("平均 MAE",f"{ts['avg_mae']:.2%}",help="一筆交易持有期間，平均曾經朝不利方向走多遠。")
    c.metric("平均 MFE",f"{ts['avg_mfe']:.2%}",help="一筆交易持有期間，平均曾經朝有利方向走多遠。")
    with st.expander("❓ MAE / MFE 是什麼？"):
        st.markdown("""
**MAE（最大不利偏移）**：進場之後，在離場以前，價格曾經對你最不利多少。

**MFE（最大有利偏移）**：進場之後，在離場以前，價格曾經對你最有利多少。

未來可以利用大量 MAE/MFE 分布研究停損與停利，但不能只挑一個歷史上最好看的數字。
""")

    st.subheader("💸 系統有沒有假裝成交很完美？")
    st.write(f"目前逐筆交易計算已加入：單邊手續費 **{fee:.2%}** ＋ 單邊滑價 **{slippage:.2%}**。")
    st.caption("滑價仍是固定假設；真實市場會隨流動性、訂單大小與波動改變。")

    st.subheader("🚦 下一步")
    if ts["trades"] < 30:
        st.warning("交易樣本仍偏少。即使目前數字漂亮，也建議增加歷史資料後再判斷。")
    elif quality["score"]>=80 and ts["expectancy"]>0:
        st.success("目前值得進一步做更長歷史與 Paper Trading 驗證，但不是實盤買入訊號。")
    else:
        st.warning(verdict["action"])

    with st.expander("📋 看每一筆交易"):
        if trades.empty: st.info("目前資料沒有形成完整交易。")
        else:
            show=trades.copy()
            for col in ["毛報酬","交易成本","淨報酬","MAE","MFE"]:
                show[col]=show[col].map(lambda x:f"{x:.2%}")
            st.dataframe(show,use_container_width=True)
else:
    st.header("🔬 專業交易分析")
    cols=st.columns(6)
    vals=[("Trades",ts["trades"]),("Win Rate",f"{ts['win_rate']:.2%}"),
          ("Avg Win",f"{ts['avg_win']:.2%}"),("Avg Loss",f"{ts['avg_loss']:.2%}"),
          ("Expectancy",f"{ts['expectancy']:.2%}"),("Max Losing Streak",ts["max_consecutive_losses"])]
    for c,(n,v) in zip(cols,vals): c.metric(n,v)
    cols=st.columns(5)
    pf="∞" if math.isinf(ts["profit_factor"]) else f"{ts['profit_factor']:.2f}"
    payoff="∞" if math.isinf(ts["payoff"]) else f"{ts['payoff']:.2f}"
    for c,(n,v) in zip(cols,[("Profit Factor",pf),("Payoff Ratio",payoff),
                              ("Avg Holding Bars",f"{ts['avg_holding_bars']:.1f}"),
                              ("Avg MAE",f"{ts['avg_mae']:.2%}"),("Avg MFE",f"{ts['avg_mfe']:.2%}")]):
        c.metric(n,v)
    st.subheader("策略淨值 vs Buy & Hold")
    st.line_chart(results.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
    st.subheader("逐筆交易紀錄")
    st.dataframe(trades,use_container_width=True)

st.divider()
st.caption("v0.6｜逐筆交易統計包含固定手續費與固定滑價假設。回測不保證未來績效，且目前沒有真實下單功能。")
