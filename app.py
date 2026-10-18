import streamlit as st
from config.settings import EXCHANGE, FEE_RATE
from data.history import fetch_history
from data.providers import get_asset, align_returns, CRYPTO, EQUITIES
from data.fundamentals import ALLOWED_US_STOCKS, fetch_us_financials, explain_report
from analytics.cross_asset import annualized_stats, rolling_correlation, normalized_growth, diversification_score
from indicators.basic import add_indicators
from strategies.strategy_library import STRATEGIES
from backtesting.analytics import analyze
from backtesting.trade_engine import build_trades, trade_statistics
from backtesting.validation import regime_report, walk_forward, cost_stress, validation_score
from backtesting.challenge import challenge_strategy
from alerts.engine import evaluate_price_alert, entry_score
from alerts.signal import analyze_entry_candidate
from analytics.confidence import confidence_from_challenge, combined_signal, GLOSSARY
from charts.workbench import make_chart
from charts.region_analysis import explain_region
from news.free_feed import fetch_news
from news.event_link import relevant_news, event_reactions
from news.translation import translate_headline
from news.research_assistant import analyze_headline, lookup_terms
from localization.assets import asset_label, market_label

st.set_page_config(page_title="Project Real Big Money",page_icon="💰",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:1.6rem;max-width:1250px}
[data-testid="stMetric"]{background:rgba(127,127,127,.06);border:1px solid rgba(127,127,127,.14);padding:14px;border-radius:16px}
.stButton>button{border-radius:12px;font-weight:700;min-height:45px}
div[data-testid="stExpander"]{border-radius:14px}
</style>""",unsafe_allow_html=True)
st.title("💰 Project Real Big Money")
st.caption("v0.9.12 美股財報研究室｜營收、EPS、毛利率與預期比較｜免費市場情報研究")

ZH={"SMA Cross":"均線交叉策略","RSI Reversion":"RSI 超賣反彈策略","Trend + RSI":"趨勢＋RSI 策略"}
@st.cache_data(ttl=86400,show_spinner=False)
def cached_translation(title):
    return translate_headline(title)

def display_headline(title,translate=False):
    if translate:
        translated,ok=cached_translation(title)
        if ok:
            st.write("**繁體中文參考翻譯：** "+translated)
            st.caption("英文原標題："+title)
            return
    st.write(title)

def show_news_research(headline,source="使用者輸入",published=None,url=None,translate=False):
    """Explain terms and channels without pretending to validate full articles."""
    analysis=analyze_headline(headline,source)
    st.markdown("#### 🔎 新聞白話拆解")
    display_headline(analysis["headline"],translate)
    timestamp=published.strftime("%Y-%m-%d %H:%M %Z") if published else "未提供"
    st.caption("來源："+source+"｜來源標示的發布時間："+timestamp)
    st.info("資料來源判讀："+analysis["source_note"])
    if url:
        st.link_button("開啟原文核對 ↗",url)
    if analysis["unclassified"]:
        st.warning("僅憑這段文字無法辨識明確的事件類別；不會硬猜利多或利空。請查原文及市場資料。")
    else:
        for ev in analysis["events"]:
            with st.container(border=True):
                st.markdown("**可能涉及的事件："+ev["name"]+"**")
                st.write("**可能影響的因素：** "+ev["channel"])
                st.write("**兩面情境：** "+ev["possible"])
                st.write("**下一步查核：**")
                for question in ev["verify"]:
                    st.write("• "+question)
    if analysis["terms"]:
        with st.expander("📖 這則新聞出現的金融英文與中文解釋",expanded=True):
            for term in analysis["terms"]:
                st.markdown("**"+term["english"]+"｜"+term["chinese"]+"**")
                st.write(term["meaning"])
                st.caption("查核重點："+term["verify"])
    else:
        st.caption("這則標題沒有命中目前的術語詞典。可切換金融詞典查詢其他詞彙。")
    with st.expander("⚠️ 這份解讀有哪些限制？"):
        for caution in analysis["caveats"]:
            st.write("• "+caution)
        st.write("**技術方式：** 使用本機關鍵字規則產生研究問題，不使用付費 AI 模型；不是全文事實查核或即時行情驗證。")

page=st.segmented_control("你今天想做什麼？",["📈 K 線研究室","📰 全球金融快報","📚 金融研究助手","🧾 美股財報研究室","🌎 市場比較","🧪 策略研究","🔥 挑戰策略","🧠 訊號可信度","🔔 價格提醒"],default="📈 K 線研究室")
st.divider()

if page=="📈 K 線研究室":
    st.header("📈 K 線研究室｜圖上看到什麼，系統就解釋什麼")
    st.info("🌱 K 線每根柱子代表一段時間內的開盤、最高、最低與收盤價格；綠紅顏色只表示該段漲跌，並不是買賣建議。")
    a,b,d=st.columns(3)
    with a: market=st.selectbox("市場",["Crypto","美股","台股"],format_func=market_label)
    with b:
        symbols={"Crypto":["BTC/USDT","ETH/USDT","SOL/USDT"],"美股":["AAPL","NVDA","SPY","QQQ"],"台股":["2330.TW","0050.TW","2317.TW","2454.TW"]}
        symbol=st.selectbox("標的",symbols[market],format_func=asset_label)
    with d: timeframe=st.selectbox("K 線週期",["1d","4h","1h"] if market=="Crypto" else ["1d"],format_func=lambda x:{"1d":"日 K（一天一根）","4h":"4 小時 K","1h":"1 小時 K"}[x])
    show_trf=st.checkbox("顯示 Twin Range Filter（雙重區間濾波器）",value=True)
    if st.toggle("📊 載入 K 線與白話分析",value=False,help="開啟後可持續框選；關閉則停止顯示圖表。"):
        try:
            with st.spinner("正在取得行情與計算指標…"):
                if market=="Crypto":
                    raw=fetch_history(EXCHANGE,symbol,timeframe,1)
                else:
                    import yfinance as yf
                    x=yf.download(symbol,period="1y",interval="1d",auto_adjust=True,progress=False)
                    if hasattr(x.columns,"nlevels") and x.columns.nlevels>1: x.columns=x.columns.get_level_values(0)
                    raw=x.reset_index().rename(columns={"Date":"timestamp","Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
                    raw.columns=[str(z).lower() for z in raw.columns]
                if raw is None or raw.empty or len(raw)<20:
                    st.warning("行情資料不足，請稍後重試或換一個標的。")
                else:
                    fig,messages=make_chart(raw,asset_label(symbol),show_trf=show_trf)
                    st.caption("在圖表工具列選擇「框選」並拖曳 K 線；也可以在下方手動指定起訖 K 線。")
                    event=st.plotly_chart(fig,use_container_width=True,key="research_chart",on_select="rerun",selection_mode="box")
                    chosen=[]
                    if event is not None:
                        for point in event.selection.points:
                            if point.get("curve_number")==next((i for i,t in enumerate(fig.data) if t.name=="框選 K 線"),-1):
                                chosen.append(point.get("customdata",point.get("point_index")))
                    chosen=[int(v) for v in chosen if v is not None]
                    with st.expander("🔎 分析指定 K 線區間",expanded=len(chosen)>=3):
                        if len(chosen)>=3:
                            start_idx,end_idx=min(chosen),max(chosen)
                            st.success("已框選 K 線，分析連續區段。")
                        else:
                            st.caption("請框選至少 3 根 K 線，或指定下方的起訖位置。")
                            start_idx=st.number_input("起始 K 線位置（從 1 開始）",min_value=1,max_value=len(raw)-2,value=max(1,len(raw)-30),step=1)-1
                            end_idx=st.number_input("結束 K 線位置（從 1 開始）",min_value=3,max_value=len(raw),value=len(raw),step=1)-1
                        if end_idx-start_idx>=2:
                            st.caption("期間："+str(raw["timestamp"].iloc[start_idx])+" ～ "+str(raw["timestamp"].iloc[end_idx]))
                            for sentence in explain_region(raw,start_idx,end_idx): st.write("• "+sentence)
                        else:
                            st.warning("請至少選取連續 3 根 K 線。")
                    st.markdown("#### 📰 新聞與 K 線連動（研究功能）")
                    translate_chart_news=st.checkbox(
                        "將相關英文新聞標題翻成繁體中文（最多 6 則）",value=False,
                        help="只有標題會傳送至外部免費翻譯服務，並保留英文原文；翻譯可能有誤。"
                    )
                    st.caption("目前僅對 Crypto 顯示事件後 K 線的觀察值。股票跨時區與休市時段需更精確處理，暫不提供事件報酬。")
                    if market=="Crypto":
                        @st.cache_data(ttl=120,show_spinner=False)
                        def chart_news():
                            return fetch_news("加密貨幣",60)
                        news_items,news_errors=chart_news()
                        matches=relevant_news(news_items,symbol)
                        reactions=event_reactions(raw,matches,8,timeframe=timeframe)
                        if news_errors: st.caption("部分新聞來源暫時無法連線："+ "、".join(news_errors))
                        if not matches:
                            st.info("免費來源目前沒有找到標題直接提到這個標的的新聞。這不代表市場沒有消息。")
                        elif not reactions:
                            st.info("有相關新聞，但目前沒有足夠的事件後完整 K 線可比較；不顯示報酬。")
                        else:
                            st.warning("⚠️ 下列數值是『新聞發布後第一根可對應 K 線的開收盤變化』，不是新聞造成的報酬，也不是事件研究的因果結論。")
                            for index,ev in enumerate(reactions):
                                stamp=ev["published"].strftime("%Y-%m-%d %H:%M UTC")
                                display_headline(ev["title"],translate_chart_news and index<6)
                                st.caption(ev["source"]+"｜發布："+stamp+"｜對應 K 線變化："+format(ev["candle_return"],"+.2%"))
                                st.link_button("閱讀原始新聞 ↗",ev["url"])
                        if matches:
                            with st.container(border=True):
                                st.markdown("##### 📖 解讀與本標的相關的新聞（事件類型與專業英文）")
                                chart_index=st.selectbox("挑選新聞標題",range(min(len(matches),20)),
                                    format_func=lambda idx:matches[idx]["title"][:100],key="chart_study_index")
                                article=matches[chart_index]
                                show_news_research(article["title"],source=article["source"],
                                    published=article["published"],url=article["url"],translate=False)
                        with st.expander("🔍 為什麼沒有把每則新聞直接畫成買賣箭頭？"):
                            st.write("標題關鍵字只能建立初步關聯，不能證明消息會影響價格；免費 RSS 也可能延遲。")
                            st.write("未收盤 K 線、休市時間、資料來源時間戳與事件發布時間都可能影響結論。未來會加入精確時區校準與完整事件研究。")

                    st.markdown("#### 💡 為什麼指標這樣顯示？")
                    for message in messages: st.write("• "+message)
                    with st.expander("📚 新手詞典｜K 線、均線、MACD、布林通道與 ATR"):
                        st.write("**K 線**：一根柱子記錄某段時間的開盤、最高、最低與收盤價格。")
                        st.write("**SMA20 / SMA50**：最近 20 / 50 根 K 線的收盤平均價；用來比較短期和較長期的方向。")
                        st.write("**RSI 14**：比較最近 14 段的漲跌力道；超過 70 或低於 30 不等於一定反轉。")
                        st.write("**成交量**：這段時間買賣成交的數量，量大不一定代表價格會上漲。")
                        st.write("**EMA（指數移動平均）**：近期價格權重較高的均線，比 SMA 對新價格更敏感。")
                        st.write("**MACD（移動平均收斂發散）**：比較兩條 EMA 的差距與變化，柱狀體顯示動能差距，不是保證轉折的訊號。")
                        st.write("**布林通道**：20 根平均價上下各兩倍標準差；反映價格相對近期波動的位置。")
                        st.write("**ATR（平均真實波幅）**：衡量波動幅度，不預測價格方向；可用來輔助設定風險距離。")
                    st.caption("行情來源：Crypto 交易所公開行情／股票 Yahoo Finance。股票為研究用途，可能延遲，非交易所即時報價。")
        except Exception as e:
            st.error("K 線載入失敗，可能是行情服務暫時無回應。")
            with st.expander("進階錯誤資訊"): st.code(str(e))


elif page=="🧾 美股財報研究室":
    st.header("🧾 美股財報研究室｜用實際數字說明公司經營")
    st.info("營收、毛利率和 EPS 都來自可取得的財報資料；EPS 市場預期只會在資料提供者提供可比數字時顯示。未提供就寫明缺漏，絕不自行猜測。")
    symbol=st.selectbox("① 選擇美國上市公司",ALLOWED_US_STOCKS,format_func=asset_label,key="fundamentals_symbol")
    st.caption("目前先支援部分美國上市公司；ETF、Crypto、台股尚未納入這個財報頁面。")
    @st.cache_data(ttl=3600,show_spinner=False)
    def cached_fundamentals(ticker):
        return fetch_us_financials(ticker)
    if st.button("🔄 重新取得財報資料",help="清除一小時快取，重新向資料提供者請求。"):
        cached_fundamentals.clear()
    if st.toggle("📊 載入營收、EPS、毛利率與市場預期",value=False,key="load_financials"):
        try:
            with st.spinner("正在讀取季度財報與 EPS 公布紀錄，可能需要一些時間…"):
                report=cached_fundamentals(symbol)
            currency=report.get("currency") or "未核實"
            st.caption("資料來源："+report["source"]+"｜取得時間："+str(report["retrieved_at"])+"｜財報貨幣："+currency+"｜快取最長 1 小時。")
            st.markdown("#### ① 財務數字：以會計季度期末分類")
            quarterly=report["quarterly"]
            if quarterly.empty:
                st.warning("本次沒有可用的季度損益表；不顯示虛構的營收或獲利數字。")
            else:
                amounts=("revenue","gross_profit","operating_income","net_income")
                table=quarterly.copy()
                for col in amounts:
                    table[col]=table[col]/1_000_000
                table=table.rename(columns={
                    "period_end":"會計季度期末",
                    "revenue":"營收（百萬）",
                    "gross_profit":"毛利（百萬）",
                    "gross_margin_pct":"毛利率（%）",
                    "operating_income":"營業利益（百萬）",
                    "net_income":"淨利（百萬）",
                    "statement_eps":"財報每股盈餘",
                    "revenue_yoy_pct":"營收年增率（%）",
                })
                st.dataframe(table,use_container_width=True,hide_index=True)
                st.caption("金額以百萬為單位；幣別："+currency+"。年增率僅在可找到去年同期季度時才計算。『財報每股盈餘』與下方 EPS 公布紀錄可能採用不同調整口徑。")
                with st.expander("🔬 為什麼不能直接用毛利率判定股價？"):
                    st.write("毛利率只能反映營收扣除銷貨成本的結果；營業費用、稅費、未來財測、估值與市場原本期待都可能改變股價反應。")
            st.markdown("#### ② EPS 實際值 vs. 市場預期值")
            eps=report["eps_events"]
            if eps.empty:
                st.warning("目前無法取得可用的 EPS 公布及預期紀錄，因此無法判斷是否超出市場預期。")
            else:
                eps_table=eps.rename(columns={
                    "announcement_date":"財報公告時間（含時區）",
                    "eps_estimate":"EPS 市場預期",
                    "eps_reported":"EPS 已公布值",
                    "eps_surprise_pct":"實際相對預期差距（%）",
                    "state":"資料狀態",
                })
                st.dataframe(eps_table,use_container_width=True,hide_index=True)
                st.caption("只有同一筆公告紀錄同時具有 EPS 預期和已公布 EPS，且預期不為 0 時，才計算差距；預期值為負時以其絕對值作為分母。未來公告不視為已公布。")
                st.warning("注意：公告日 ≠ 會計季度期末日；這兩張表不可依排序直接逐列對接。Yahoo Finance 的 EPS 公布口徑也可能與損益表 Diluted EPS 不同。")
            st.markdown("#### ③ 看懂數字：不只看成長，也看不足的證據")
            for line in explain_report(report):
                st.write("• "+line)
            if report["notes"]:
                st.markdown("#### ⚠️ 資料取得限制")
                for note in report["notes"]:
                    st.write("• "+note)
            st.markdown("#### 🔗 原始資料與查核")
            st.link_button("Yahoo Finance 財報頁 ↗","https://finance.yahoo.com/quote/"+symbol+"/financials/")
            st.link_button("SEC EDGAR 官方財報搜尋 ↗","https://www.sec.gov/edgar/search/")
            st.caption("資料僅供研究。Yahoo Finance 不是 SEC 官方財報原文，數字可能延遲、重編或缺漏。財測與營收分析師共識目前尚未接入可靠來源，不會在頁面虛構。")
        except Exception as e:
            st.error("財報資料暫時無法載入；請稍後重試，或選擇其他美股。")
            with st.expander("進階錯誤資訊"):
                st.code(str(e))

elif page=="📚 金融研究助手":
    st.header("📚 繁體中文金融研究助手")
    st.info("把英文財經標題變成繁體中文術語、可能的影響管道與應查核的問題。不下買賣結論，也不宣稱已讀過新聞全文。")
    mode=st.radio("你想怎麼研究？",["自己貼上新聞標題","從免費新聞選一則","金融英文詞典"],horizontal=True)
    if mode=="自己貼上新聞標題":
        headline=st.text_area(
            "貼上英文或中文財經標題",height=100,max_chars=600,
            placeholder="例如：Nvidia beats earnings estimates but lowers revenue guidance"
        )
        st.caption("離線關鍵字解讀不會把你貼上的內容送到外部服務；只有選擇翻譯英文標題時才會使用第三方翻譯。")
        opt_translate=st.checkbox("另外翻譯這段英文標題成繁體中文",value=False,
            help="勾選後標題會送往外部免費翻譯服務；翻譯僅供參考。")
        if headline.strip():
            show_news_research(headline.strip(),translate=opt_translate)
        else:
            st.caption("輸入標題後就會出現解讀；也可以切到金融英文詞典。")
    elif mode=="從免費新聞選一則":
        research_category=st.selectbox("新聞市場",["美股","全球財經","加密貨幣","台股","全部"],key="research_category")
        @st.cache_data(ttl=120,show_spinner=False)
        def research_news(cat):
            return fetch_news(cat,40)
        with st.spinner("正在讀取公開新聞標題…"):
            selected_items,selected_errors=research_news(research_category)
        if selected_errors: st.caption("部分新聞來源不可用："+"、".join(selected_errors))
        if not selected_items:
            st.warning("暫時沒有可用的新聞標題；可以切換成手動貼上標題。")
        else:
            index=st.selectbox("想解讀哪一則？",range(len(selected_items)),
                format_func=lambda idx:selected_items[idx]["title"][:110],key="research_news_index")
            chosen=selected_items[index]
            opt_translate=st.checkbox("顯示繁體中文參考翻譯",value=False,key="research_translate",
                help="只有這一則的英文標題會送至外部免費翻譯服務。")
            show_news_research(chosen["title"],source=chosen["source"],
                published=chosen["published"],url=chosen["url"],translate=opt_translate)
    else:
        st.subheader("📖 金融英文詞典｜查意思，更要知道怎麼核對")
        query=st.text_input("搜尋英文縮寫或中文關鍵字",
            placeholder="例如 EPS、Guidance、CPI、ETF、資金費率")
        definitions=lookup_terms(query)
        st.caption(f"找到 {len(definitions)} 筆相關詞彙｜內容是一般定義，不是特定新聞的證據。")
        if not definitions:
            st.info("暫時找不到這個詞彙；請試試英文縮寫或較短的中文關鍵字。")
        else:
            for row in definitions[:25]:
                with st.expander(row["chinese"]+"（"+row["english"]+"）"):
                    st.write(row["meaning"])
                    st.caption("看財報或新聞時要注意："+row["verify"])
            if len(definitions)>25:
                st.caption("結果較多，請輸入更精確的關鍵字縮小範圍。")

elif page=="📰 全球金融快報":
    st.header("📰 全球金融快報｜免費新聞來源")
    st.info("🌱 這裡會整理公開 RSS 新聞。更新頻率不等於新聞發布速度；目前沒有保證每則新聞都能在一分鐘內出現。")
    category=st.selectbox("想看哪個市場？",["全部","全球財經","台股","美股","加密貨幣"])
    @st.cache_data(ttl=120,show_spinner=False)
    def cached_news(cat):
        return fetch_news(cat)
    if st.button("🔄 重新檢查來源"):
        cached_news.clear()
    with st.spinner("正在整理最新新聞…"):
        items,errors=cached_news(category)
    from datetime import datetime, timezone
    now=datetime.now(timezone.utc)
    st.caption("畫面檢查時間（UTC）："+now.strftime("%Y-%m-%d %H:%M")+"｜資料快取最多 2 分鐘；新聞時間以來源提供為準。")
    translate_news=st.checkbox(
        "🌐 顯示繁體中文新聞翻譯（前 8 則英文標題）",value=False,
        help="選取後才會把英文標題送往外部免費翻譯服務；不傳送完整文章或行情資料。"
    )
    if translate_news: st.caption("僅翻譯英文新聞標題；可能有誤或失敗，請以英文原文為準。")
    if errors: st.warning("部分來源暫時無法取得："+ "、".join(errors))
    if not items: st.info("目前沒有取得新聞，請稍後重試或選擇其他分類。")
    if items:
        with st.container(border=True):
            st.markdown("##### 🔍 選一則新聞：了解金融術語、可能影響與需要驗證的資料")
            study_index=st.selectbox("選擇要研究的新聞",range(min(len(items),30)),
                format_func=lambda idx:items[idx]["title"][:110],key="feed_study_index")
            study=items[study_index]
            show_news_research(study["title"],source=study["source"],
                published=study["published"],url=study["url"],translate=False)
    for index,item in enumerate(items):
        when=item["published"]
        stamp=when.astimezone().strftime("%m/%d %H:%M") if when else "未提供發布時間"
        display_headline(item["title"],translate_news and index<8)
        st.caption(item["category"]+"｜"+item["source"]+"｜"+stamp)
        st.link_button("閱讀原文 ↗",item["url"])
        st.divider()
    with st.expander("📚 新手提示｜如何判讀快訊？"):
        st.write("**發布時間**不是系統發現時間；某些 RSS 可能延後更新。")
        st.write("**新聞標題**不是已驗證的交易訊號；要核對原文與官方公告。")
        st.write("**Google News**是新聞索引，不代表所有媒體都有授權可全文轉載。這裡只提供標題及原文連結。")

elif page=="🔔 價格提醒":
    st.header("🔔 Entry Intelligence｜進場觀察中心")
    st.info("🌱 新手模式：系統不是只看價格，而是一起檢查價格、RSI、趨勢與策略訊號，再告訴你『為什麼值得看』。")
    c1,c2=st.columns(2)
    with c1:
        asset=st.selectbox("① 想觀察什麼？",list(CRYPTO),format_func=asset_label,help="目前先支援 BTC、ETH、SOL。")
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

elif page=="🧠 訊號可信度":
    st.header("🧠 Signal Confidence｜這個訊號值得相信多少？")
    st.info("🌱 新手提示：**Entry Score 看『現在』，Confidence Score 看『過去驗證是否站得住腳』。兩個都高，才比較值得進一步研究。")
    c1,c2=st.columns(2)
    with c1:
        symbol=st.selectbox("① 選擇加密貨幣",["BTC/USDT","ETH/USDT","SOL/USDT"],format_func=asset_label,key="conf_symbol")
        strategy=st.selectbox("② 選擇策略",list(STRATEGIES),index=2,format_func=lambda x:ZH[x],key="conf_strategy",help="新手建議先從趨勢＋RSI開始。")
        years=st.select_slider("③ 用幾年歷史資料驗證？",[1,2,3,5],value=3,key="conf_years",format_func=lambda x:f"{x}年")
    with c2:
        st.markdown("#### 📖 先看懂兩個分數")
        st.write("**Entry Score（進場條件分數）**：現在這一刻，看起來有多少條件同時支持。")
        st.write("**Confidence Score（訊號可信度分數）**：這套策略以前接受不同測試時，有多少證據支持它不是只靠運氣。")
        st.warning("⚠️ 80 分不是 80% 勝率，也不是 80% 機率會漲。")
    if st.button("🧠 檢查訊號可信度",type="primary",use_container_width=True):
        try:
            with st.spinner("正在讓策略接受歷史資料、不同市場環境與壓力測試…"):
                raw=fetch_history(EXCHANGE,symbol,"1d",years)
                sig=STRATEGIES[strategy](add_indicators(raw))
                current=float(sig["close"].iloc[-1])
                intel=analyze_entry_candidate(raw,strategy,timeframe="1d")
                entry,label,entry_reasons,entry_cautions=entry_score(False,intel["signal"],intel["rsi"],None,intel["trend_up"])
                entry_cautions=[x for x in entry_cautions if "價格尚未進入" not in x]
                entry_cautions.append("本頁未設定觀察價：價格條件不計分，最高只有 45 分；勿與有設定觀察價的分數直接比較。")
                challenge=challenge_strategy(sig,float(FEE_RATE),"1d",0.0005)
                confidence,conf_label,conf_reasons,conf_cautions=confidence_from_challenge(challenge)
                combined,verdict,explanation=combined_signal(entry,confidence)
            m=st.columns(3)
            m[0].metric("Entry Score｜現在條件",str(entry)+"/100",help=GLOSSARY["Entry Score"])
            m[1].metric("Confidence Score｜歷史可信度",str(confidence)+"/100",help=GLOSSARY["Confidence Score"])
            m[2].metric("綜合觀察分數",str(combined)+"/100",help="Entry Score 佔 55%，Confidence Score 佔 45%。這是研究排序工具，不是獲利機率。")
            if combined>=80: st.success("🟢 **"+verdict+"**｜"+explanation)
            elif combined>=60: st.info("🔵 **"+verdict+"**｜"+explanation)
            else: st.warning("🟡 **"+verdict+"**｜"+explanation)
            a,b=st.columns(2)
            with a:
                st.markdown("#### ✅ 為什麼系統願意加分？")
                for x in entry_reasons+conf_reasons: st.write("• "+x)
                if not entry_reasons and not conf_reasons: st.write("目前沒有足夠的加分理由。")
            with b:
                st.markdown("#### ❓ 為什麼不是 100 分？")
                problems=entry_cautions+conf_cautions
                for x in problems: st.write("• "+x)
                if not problems: st.write("目前測試沒有明顯扣分項，但未來市場仍可能與歷史不同。")
            with st.expander("📚 新手字典｜看不懂專有名詞就打開這裡"):
                for term,plain in GLOSSARY.items():
                    st.markdown("**"+term+"**")
                    st.write(plain)
            with st.expander("🔬 進階資料｜Challenge 測試明細"):
                st.dataframe(challenge["checks"],use_container_width=True,hide_index=True)
                st.caption("Challenge Score："+str(challenge["score"])+"/100｜"+GLOSSARY["Challenge Score"])
        except Exception as e:
            st.error("可信度分析暫時無法完成。可能是市場資料來源暫時無回應；請稍後再試。")
            with st.expander("技術錯誤（進階使用者）"): st.code(str(e))

elif page=="🌎 市場比較":
    with st.sidebar:
        st.header("🌎 市場比較")
        ta=st.selectbox("A 類型",["美股","Crypto"],format_func=market_label); la=EQUITIES if ta=="美股" else list(CRYPTO)
        aa=st.selectbox("資產 A",la,index=1 if ta=="美股" else 0,format_func=asset_label)
        tb=st.selectbox("B 類型",["Crypto","美股"],format_func=market_label); lb=list(CRYPTO) if tb=="Crypto" else EQUITIES
        ab=st.selectbox("資產 B",lb,format_func=asset_label)
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
    for col,(n,v) in zip(c,[(asset_label(aa),f"{s['a']['annual_return']:.1%}"),(asset_label(ab),f"{s['b']['annual_return']:.1%}"),("相關性",f"{corr:.2f}"),("分散分數",f"{ds}/100")]): col.metric(n,v)
    t1,t2,t3=st.tabs(["📈 成長","🛡️ 風險","🔗 關係"])
    with t1:
        chart=growth[["date","A","B"]].rename(columns={"A":asset_label(aa),"B":asset_label(ab)}).set_index("date"); st.line_chart(chart)
    with t2:
        st.dataframe([{"資產":asset_label(aa),**s["a"]},{"資產":asset_label(ab),**s["b"]}],use_container_width=True,hide_index=True)
    with t3:
        st.line_chart(roll.set_index("date")[["rolling_corr"]]); st.caption(f"{dl}｜{ds}/100")
    st.caption("跨資產統計使用共同日期。Crypto 週末資訊不會直接與美股休市日比較。")

else:
    with st.sidebar:
        st.header("🧪 策略設定" if page=="🧪 策略研究" else "🔥 挑戰設定")
        symbol=st.selectbox("加密貨幣",["BTC/USDT","ETH/USDT","SOL/USDT"],format_func=asset_label)
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
st.caption("Project Real Big Money v0.9.12 Earnings and Fundamentals｜研究用途，不構成投資建議；PASS 不代表應投入真實資金。")
