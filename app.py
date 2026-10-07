import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.history import fetch_history
from data.providers import get_asset, align_returns, CRYPTO, EQUITIES
from analytics.cross_asset import annualized_stats, rolling_correlation, normalized_growth, diversification_score
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze
from backtesting.trade_engine import build_trades, trade_statistics
from backtesting.validation import regime_report, walk_forward, cost_stress, validation_score
from backtesting.challenge import challenge_strategy
from alerts.engine import evaluate_price_alert, entry_score
from alerts.signal import analyze_entry_candidate

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:1.6rem;max-width:1250px}
[data-testid="stMetric"]{background:rgba(127,127,127,.06);border:1px solid rgba(127,127,127,.14);padding:14px;border-radius:16px}
.stButton>button{border-radius:12px;font-weight:700;min-height:45px}
div[data-testid="stExpander"]{border-radius:14px}
</style>""",unsafe_allow_html=True)
st.title("💰 Project Real Big Money")
st.caption("v0.9.4 Entry Intelligence｜價格 + RSI + 趨勢 + 策略 → Entry Score")

ZH={"SMA Cross":"均線交叉策略","RSI Reversion":"RSI 超賣反彈策略","Trend + RSI":"趨勢＋RSI 策略"}
page=st.segmented_control("你今天想做什麼？",["🌎 市場比較","🧪 策略研究","🔥 挑戰策略","🔔 價格提醒"],default="🌎 市場比較")
st.divider()

if page=="🔔 價格提醒":
    st.header("🔔 Entry Intelligence｜進場觀察中心")
    st.info("🌱 新手模式：系統不是只看價格，而是一起檢查價格、RSI、趨勢與策略訊號，再告訴你『為什麼值得看』。")
    c1,c2=st.columns(2)
    with c1:
        asset=st.selectbox("① 想觀察什麼？",list(CRYPTO),help="目前先支援 BTC、ETH、SOL。")
        target=st.number_input("② 觀察價格",min_value=0.01,value=60000.0,help="這不是預測價格，而是你希望系統開始提高注意力的門檻。")
        direction=st.radio("③ 觸發方式",["跌到這個價格以下","突破這個價格以上"],help="想找回檔觀察區可選『以下』；想看突破可選『以上』。")
        strategy_name=st.selectbox("④ 確認策略",list(STRATEGIES),index=2,format_func=lambda x:ZH[x],help="新手建議先用『趨勢＋RSI』。")
    with c2:
        st.markdown("#### 📖 Entry Score 怎麼看？")
        st.write("**80–100：高優先觀察**｜多個條件同時支持。")
        st.write("**60–79：候選觀察區**｜有支持條件，但仍需確認風險。")
        st.write("**40–59：持續觀察**｜條件還不完整。")
        st.write("**0–39：條件不足**｜目前沒有必要急著行動。")
        st.caption("Entry Score 不是上漲機率，也不是『買進勝率』。")
    if st.button("🔎 分析現在的進場條件",type="primary",use_container_width=True):
        try:
            with st.spinner("正在取得市場資料並分析 RSI、趨勢與策略訊號…"):
                raw=get_asset(asset,"Crypto",1,"1d")
                if raw.empty:
                    st.error("目前拿不到市場資料。這通常是資料來源暫時無回應，不代表你的設定錯誤。")
                    st.stop()
                current=float(raw["close"].iloc[-1])
                price_result=evaluate_price_alert(current,target,"below" if direction.startswith("跌") else "above")
                intel=analyze_entry_candidate(raw,strategy_name,timeframe="1d")
                score,label,reasons,cautions=entry_score(price_result.triggered,intel["signal"],intel["rsi"],intel["challenge_score"],intel["trend_up"])
            cols=st.columns(4)
            cols[0].metric("目前價格","$"+format(current,",.2f"))
            cols[1].metric("RSI","—" if intel["rsi"] is None else format(intel["rsi"],".1f"),help="RSI 常用來觀察市場是否偏熱或偏冷；不是單獨的買賣訊號。")
            cols[2].metric("趨勢","偏多" if intel["trend_up"] else "偏弱",help="目前以 SMA20 與 SMA50 的相對位置做簡化判斷。")
            cols[3].metric("Entry Score",str(score)+"/100")
            if score>=80: st.success("🟢 "+label+"｜多個條件同時支持，但仍要先決定可承受風險。")
            elif score>=60: st.info("🔵 "+label+"｜值得提高注意，但還不是『一定要買』。")
            elif score>=40: st.warning("🟡 "+label+"｜目前條件還沒有完全聚合。")
            else: st.error("⚪ "+label+"｜目前不需要因為害怕錯過而追進。")
            a,b=st.columns(2)
            with a:
                st.markdown("#### ✅ 系統支持理由")
                if reasons:
                    for x in reasons: st.write("• "+x)
                else: st.write("目前沒有明確支持條件。")
            with b:
                st.markdown("#### ⚠️ 需要注意")
                if cautions:
                    for x in cautions: st.write("• "+x)
                else: st.write("目前沒有額外警示，但仍需自行設定風險上限。")
            with st.expander("🔬 專業資訊｜系統到底算了什麼？"):
                st.write("價格條件最高 40 分、策略多方訊號 20 分、RSI 15 分、趨勢 10 分；Challenge 驗證未在快速分析中執行，之後可再加入最高 15 分。")
                st.write("策略訊號使用前一版策略庫；趨勢以 SMA20 > SMA50 判斷。這些規則是研究框架，不代表未來報酬。")
        except Exception as e:
            st.error("分析暫時無法完成。請稍後重試；若持續發生，再查看終端機錯誤訊息。")
            with st.expander("技術錯誤（進階使用者）"): st.code(str(e))
    st.caption("📧 Gmail 通知設定可以先略過，不影響 Entry Intelligence 分析。")

elif page=="🌎 市場比較":
    with st.sidebar:
        st.header("🌎 市場比較")
        ta=st.selectbox("A 類型",["美股","Crypto"]); la=EQUITIES if ta=="美股" else list(CRYPTO)
        aa=st.selectbox("資產 A",la,index=1 if ta=="美股" else 0)
        tb=st.selectbox("B 類型",["Crypto","美股"]); lb=list(CRYPTO) if tb=="Crypto" else EQUITIES
        ab=st.selectbox("資產 B",lb)
        years=st.select_slider("期間",[1,2,3,5],value=3,format_func=lambda x:f"{x}年")
        run=st.button("開始比較 →",type="primary",use_container_width=True)
    if not run:
        st.subheader("把不同市場放在同一把尺上")
        st.write("第一次建議 **QQQ × BTC × 3年**。先看結論，再展開專業數據。"); st.stop()
    with st.spinner("正在對齊市場資料…"):
        a=get_asset(aa,"Crypto" if ta=="Crypto" else "Equity",years,"1d")
        b=get_asset(ab,"Crypto" if tb=="Crypto" else "Equity",years,"1d")
        aligned=align_returns(a,b); s=annualized_stats(aligned)
    if not s: st.error("資料不足。"); st.stop()
    growth=normalized_growth(aligned); roll=rolling_correlation(aligned,30); ds,dl=diversification_score(s["correlation"])
    corr=s["correlation"]
    if corr>=.7: st.warning(f"**分散效果可能有限**｜相關性 {corr:.2f}")
    elif corr>=.3: st.info(f"**有一些分散效果**｜相關性 {corr:.2f}")
    else: st.success(f"**潛在分散效果較高**｜相關性 {corr:.2f}")
    c=st.columns(4)
    for col,(n,v) in zip(c,[(aa,f"{s['a']['annual_return']:.1%}"),(ab,f"{s['b']['annual_return']:.1%}"),("相關性",f"{corr:.2f}"),("分散分數",f"{ds}/100")]): col.metric(n,v)
    t1,t2,t3=st.tabs(["📈 成長","🛡️ 風險","🔗 關係"])
    with t1:
        chart=growth[["date","A","B"]].rename(columns={"A":aa,"B":ab}).set_index("date"); st.line_chart(chart)
    with t2:
        st.dataframe([{"資產":aa,**s["a"]},{"資產":ab,**s["b"]}],use_container_width=True,hide_index=True)
    with t3:
        st.line_chart(roll.set_index("date")[["rolling_corr"]]); st.caption(f"{dl}｜{ds}/100")
    st.caption("跨資產統計使用共同日期。Crypto 週末資訊不會直接與美股休市日比較。")

else:
    with st.sidebar:
        st.header("🧪 策略設定" if page=="🧪 策略研究" else "🔥 挑戰設定")
        symbol=st.selectbox("Crypto",["BTC/USDT","ETH/USDT","SOL/USDT"])
        timeframe=st.selectbox("週期",["1h","4h","1d"])
        years=st.select_slider("歷史",[1,2,3,5],value=3,format_func=lambda x:f"{x}年")
        strategy=st.selectbox("策略",list(STRATEGIES),format_func=lambda x:ZH[x])
        fee=st.number_input("單邊手續費",0.0,0.01,float(FEE_RATE),0.0001,format="%.4f")
        slip=st.number_input("單邊滑價",0.0,0.01,0.0005,0.0001,format="%.4f")
        run=st.button("開始研究 →" if page=="🧪 策略研究" else "🔥 挑戰這個策略",type="primary",use_container_width=True)
    if not run:
        if page=="🧪 策略研究": st.info("先回答：策略以前有沒有優勢、風險多大、跨環境是否穩定。")
        else: st.warning("這裡不幫策略找優點；系統會主動尋找它失效的地方。")
        st.stop()
    with st.spinner("正在下載多年資料並分析…"):
        raw=fetch_history(EXCHANGE,symbol,timeframe,years); sig=STRATEGIES[strategy](add_indicators(raw))
    if page=="🧪 策略研究":
        equity,m=analyze(sig,fee,timeframe); trades=build_trades(sig,fee,slip); ts=trade_statistics(trades)
        regimes=regime_report(sig,fee,timeframe); wf=walk_forward(sig,fee,timeframe,5); stress=cost_stress(sig,fee,timeframe,slip)
        score,status,reasons=validation_score(years,ts,wf,regimes,stress); icon={"PASS":"🟢","WATCH":"🟡","FAIL":"🔴"}[status]
        st.header(f"{icon} 策略驗證 {score}/100｜{status}")
        st.caption("分數不是獲利機率。")
        c=st.columns(4)
        for col,(n,v) in zip(c,[("完整交易",ts["trades"]),("逐筆勝率",f"{ts['win_rate']:.1%}"),("每筆期望",f"{ts['expectancy']:.2%}"),("最大回撤",f"{m['max_drawdown']:.1%}")]): col.metric(n,v)
        tabs=st.tabs(["📈 淨值","🌦️ 市場環境","🚶 Walk-Forward","💸 成本壓力"])
        with tabs[0]: st.line_chart(equity.set_index("timestamp")[["strategy_equity","buy_hold_equity"]])
        for tab,data in zip(tabs[1:],[regimes,wf,stress]):
            with tab: st.dataframe(data,use_container_width=True,hide_index=True)
        for r in reasons: st.warning(r)
    else:
        with st.spinner("正在用 Bootstrap、Monte Carlo、跨年份與壓力測試反證…"): r=challenge_strategy(sig,fee,timeframe,slip)
        icon={"PASS":"🟢","WATCH":"🟡","FAIL":"🔴"}[r["status"]]
        st.header(f"{icon} Challenge Score {r['score']}/100｜{r['status']}")
        st.caption("不是成功機率，而是目前撐過多少反證測試。")
        st.dataframe(r["checks"],use_container_width=True,hide_index=True)
        b=r["bootstrap"]; mc=r["monte_carlo"]; c=st.columns(3)
        c[0].metric("Bootstrap 正期望",f"{b['positive_probability']:.1%}")
        c[1].metric("期望值 90% 區間",f"{b['p05']:.2%} ～ {b['p95']:.2%}")
        c[2].metric("Monte Carlo 壓力回撤",f"{mc['p95_worst_dd']:.1%}")
        tabs=st.tabs(["年份","市場環境","Walk-Forward","成本壓力"])
        for tab,data in zip(tabs,[r["yearly"],r["regimes"],r["walk_forward"],r["stress"]]):
            with tab: st.dataframe(data,use_container_width=True,hide_index=True)

st.divider()
st.caption("Project Real Big Money v0.9.4 Entry Intelligence｜研究用途，不構成投資建議；PASS 不代表應投入真實資金。")
