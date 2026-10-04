import math
import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze, split_validation
from backtesting.quality import quality_score, beginner_verdict

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide")
st.title("💰 Project Real Big Money")
st.caption("v0.5｜新手友善回測＋策略品質中心｜研究用途，不會自動下單")

ZH={"SMA Cross":"均線交叉策略","RSI Reversion":"RSI 超賣反彈策略","Trend + RSI":"趨勢＋RSI 策略"}
HELP={
"SMA Cross":"比較短期與長期平均價格，觀察市場趨勢方向。",
"RSI Reversion":"尋找價格可能過度下跌後的反彈機會。",
"Trend + RSI":"同時看趨勢與市場強弱，條件比單一指標嚴格。"}

with st.sidebar:
    st.header("⚙️ 設定")
    mode=st.radio("顯示模式",["🌱 新手模式","🔬 專業模式"],help="新手模式先說人話；專業模式顯示更多統計資料。")
    symbol=st.selectbox("我要研究哪個幣？",["BTC/USDT","ETH/USDT","SOL/USDT"])
    timeframe=st.selectbox("多久看一次價格？",["15m","1h","4h","1d"],index=1,help="例如 1h 表示每一根 K 線代表一小時。新手建議先用 1h。")
    strategy=st.selectbox("使用哪個策略？",list(STRATEGIES),format_func=lambda x:ZH[x])
    st.caption("💡 "+HELP[strategy])
    limit=st.slider("要看多少根歷史 K 線？",200,1000,500,100,help="越多通常越有參考價值，但 1000 根仍不代表足夠涵蓋完整牛熊週期。")
    fee=st.number_input("交易成本",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f",help="0.001 = 0.1%。不要把交易成本設成 0，否則容易高估策略。")
    run=st.button("▶ 開始回測",type="primary",use_container_width=True)

with st.expander("🎓 我完全不懂回測，從這裡開始",expanded=False):
    st.markdown("""
**回測是什麼？** 把一套交易規則放進過去的市場資料，看它以前會發生什麼。

**它不能證明未來會賺錢。** 回測的用途是淘汰明顯不好的策略，並檢查策略是否值得繼續研究。

第一次使用建議：BTC/USDT → 1h → 保持其他預設值 → 開始回測。
""")

if not run:
    st.info("👈 第一次使用？保持預設值直接按「開始回測」即可。")
    st.markdown("### 系統會替你回答四個問題")
    a,b,c,d=st.columns(4)
    a.info("💰 **以前有賺嗎？**\n\n先看歷史結果。")
    b.info("🛡️ **中間多痛？**\n\n看最大資金下跌。")
    c.info("🧪 **可信嗎？**\n\n檢查資料與樣本外結果。")
    d.info("🚦 **下一步？**\n\n告訴你該繼續研究還是淘汰。")
    st.stop()

with st.spinner("正在取得資料並進行回測…"):
    raw=fetch_ohlcv(EXCHANGE,symbol,timeframe,limit)
    base=add_indicators(raw)
    signals=STRATEGIES[strategy](base)
    results,metrics=analyze(signals,fee,timeframe)
    _,train_m,test,test_m=split_validation(signals,fee,timeframe)
    quality=quality_score(metrics,train_m,test_m,len(results))
    verdict=beginner_verdict(metrics,quality)

st.success(f"分析完成｜{symbol}｜{ZH[strategy]}｜{timeframe}")

if mode=="🌱 新手模式":
    st.header("📋 先看結論")
    st.markdown(f"## {quality['icon']} 回測品質：{quality['score']} / 100｜{quality['level']}")
    st.progress(quality["score"]/100)
    st.caption("這個分數不是『賺錢機率』，而是目前回測證據的完整程度與可信度提示。")

    a,b=st.columns(2)
    with a:
        st.subheader("💰 過去有賺錢嗎？")
        st.metric("策略歷史報酬",f"{metrics['total_return']:.2%}")
        diff=metrics["total_return"]-metrics["buy_hold"]
        if metrics["total_return"]>0:
            st.success("這段歷史資料中，策略最後是正報酬。")
        else:
            st.error("這段歷史資料中，策略最後是虧損。")
        st.write(f"與單純持有相比，相差 **{diff:+.2%}**。這不是未來報酬預測。")
    with b:
        st.subheader("🛡️ 中間可能有多痛？")
        dd=abs(metrics["max_drawdown"])
        st.metric("歷史最大回撤",f"-{dd:.2%}")
        st.write(f"如果用 **10 萬元**理解，歷史上從策略資金高點出發，曾出現約 **{100000*dd:,.0f} 元**的回落幅度。")
        st.caption("這只是把百分比換成容易理解的金額；未來損失可能更大。")

    st.subheader("🧪 為什麼系統給這個品質分數？")
    for name,score in quality["parts"].items():
        maxv={"資料量":20,"交易樣本":15,"風險控制":15,"風險調整績效":15,"獲利品質":15,"樣本外驗證":20}[name]
        icon="🟢" if score/maxv>=.7 else "🟡" if score/maxv>=.4 else "🔴"
        st.write(f"{icon} **{name}：{score:.0f}/{maxv}**")
    with st.expander("❓ 這些項目到底是什麼？"):
        st.markdown("""
- **資料量**：歷史資料太短，可能只是碰巧遇到適合策略的行情。
- **交易樣本**：只有幾筆交易就說策略有效，可信度很低。
- **風險控制**：觀察策略歷史上曾經跌得多深。
- **風險調整績效**：不是只看賺多少，也看為了賺這些錢承受多少波動。
- **獲利品質**：檢查正報酬是否足以覆蓋負報酬。
- **樣本外驗證**：把後段資料當成策略「沒看過的考題」，降低只背歷史答案的風險。
""")
    st.subheader("🚦 那我現在應該做什麼？")
    if quality["score"]>=80 and metrics["total_return"]>0:
        st.success(verdict["action"])
    elif quality["score"]>=60:
        st.warning(verdict["action"])
    else:
        st.error(verdict["action"])
    st.info("⚠️ 『值得繼續研究』不等於『現在應該買』。v0.5 不提供真實下單。")

    with st.expander("📈 我想看看圖表"):
        st.write("**策略 vs 單純持有**：兩條線都從 1 開始，最後較高代表這段期間累積表現較好。")
        st.line_chart(results.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
        st.write("**價格與均線**：用來觀察策略所看到的趨勢。")
        st.line_chart(base.set_index("timestamp")[["close","sma_20","sma_50"]])
else:
    st.header("🔬 專業研究面板")
    c=st.columns(7)
    vals=[("策略報酬",metrics["total_return"],".2%"),("Buy & Hold",metrics["buy_hold"],".2%"),
          ("最大回撤",metrics["max_drawdown"],".2%"),("Sharpe",metrics["sharpe"],".2f"),
          ("Sortino",metrics["sortino"],".2f"),("勝率*",metrics["win_rate"],".1%"),
          ("Profit Factor",metrics["profit_factor"],".2f")]
    for col,(n,v,f) in zip(c,vals):
        col.metric(n, "∞" if n=="Profit Factor" and math.isinf(v) else format(v,f))
    st.caption("*目前勝率仍是持倉期間正報酬 K 線比例，尚不是完整逐筆交易勝率；後續 Trade Engine 將修正。")
    st.subheader("70/30 樣本外驗證")
    a,b,c,d=st.columns(4)
    a.metric("前 70% 報酬",f"{train_m['total_return']:.2%}")
    b.metric("後 30% 報酬",f"{test_m['total_return']:.2%}")
    c.metric("後 30% Sharpe",f"{test_m['sharpe']:.2f}")
    d.metric("後 30% 最大回撤",f"{test_m['max_drawdown']:.2%}")
    st.subheader("策略 vs Buy & Hold")
    st.line_chart(results.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
    st.subheader("價格 / SMA20 / SMA50")
    st.line_chart(base.set_index("timestamp")[["close","sma_20","sma_50"]])
    st.subheader("RSI 14")
    st.line_chart(base.set_index("timestamp")[["rsi_14"]])
    with st.expander("原始回測明細"):
        st.dataframe(results.tail(200),use_container_width=True)

st.divider()
st.caption("Project Real Big Money v0.5｜回測只能描述歷史情境，不保證未來結果。本工具目前沒有真實下單功能。")
