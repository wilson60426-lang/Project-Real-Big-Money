"""PRBM bilingual financial headline research helper (transparent rule-based MVP).

NO LLM / prediction / article crawling. Only the headline provided by the user
or already fetched RSS title is analyzed. Never assert that a title is verified,
that a headline CAUSED a price change, or that an event guarantees a direction.
"""
import re

# Each term has a plain Chinese explanation and a fact-check prompt.
TERMS = {
    "EPS": ("每股盈餘", "公司淨利分攤到每股普通股的數字；須確認採用哪一種 EPS 口徑。", "核對實際值、分析師預期、去年同期與是否調整。", ("EPS", "earnings per share", "每股盈餘")),
    "Revenue": ("營收", "公司銷售商品或服務所認列的收入，不等於賺到的淨利。", "確認年增率、預估值、幣別與匯率效果。", ("revenue", "sales", "營收")),
    "Earnings": ("財報／盈餘", "公司發布的營運與獲利數據，需區分季報、年報及預測。", "先看財報期間、實際數字、預估及非經常項目。", ("earnings", "quarterly results", "financial results", "財報")),
    "Guidance": ("財測／展望", "公司對未來業績的預估，具有不確定性，也可能與市場預期不同。", "區分營收財測、獲利財測及華爾街原本的預估。", ("guidance", "outlook", "forecast", "財測", "財測指引")),
    "Consensus": ("市場預期值", "分析師預估的彙整值；實際值高於預期，不代表股價一定漲。", "確認共識值統計時間、樣本與比較基準。", ("consensus", "estimates", "expectations", "市場預期")),
    "Beat / Miss": ("優於／低於預期", "描述實際財報是否高於或低於市場預估，需核對是營收還是盈餘。", "驗證實際值與一致預期；也要檢查未來財測。", ("beats estimates", "beat estimates", "misses estimates", "missed estimates", "earnings beat", "earnings miss", "優於預期", "低於預期")),
    "GAAP": ("一般公認會計原則", "依會計準則編製的財務數據，與公司自訂的調整後數字可能不同。", "確認 GAAP 與 Non-GAAP 差異和排除項目。", ("GAAP", "公認會計原則")),
    "Non-GAAP": ("非一般公認會計原則數字", "公司調整後的業績數字，可能排除股權薪酬等費用；不宜只看單一口徑。", "回查公司提供的 GAAP 調節表。", ("non-gaap", "adjusted earnings", "調整後盈餘")),
    "Gross Margin": ("毛利率", "營收扣除銷貨成本後，毛利占營收的比例。", "對照去年與上季、產品組合及成本變化。", ("gross margin", "毛利率")),
    "Operating Margin": ("營業利益率", "衡量本業經營獲利效率的比例，通常不包含部分業外損益。", "核對費用、一次性項目與定義。", ("operating margin", "營業利益率")),
    "Net Income": ("淨利", "公司扣除成本、費用與稅負等後的最終獲利。", "區分本業成長與一次性收益。", ("net income", "net profit", "淨利")),
    "Free Cash Flow (FCF)": ("自由現金流", "營業現金流扣除資本支出後的概念，可觀察營運產生現金的能力。", "確認公司 FCF 定義、資本支出和現金流的季節性。", ("free cash flow", "FCF", "自由現金流")),
    "EBITDA": ("稅息折舊攤銷前利益", "排除利息、稅、折舊和攤銷的指標；不是現金流，也不能取代淨利。", "注意負債、資本支出及調整項目。", ("EBITDA",)),
    "P/E": ("本益比", "股價相對每股盈餘的倍數；獲利為負時可能不適用。", "區分歷史本益比與預估本益比。", ("P/E", "price-to-earnings", "本益比")),
    "YoY": ("年增率", "與去年同期比較的變動幅度。", "區分基期效果、實際值與季節性。", ("YoY", "year-over-year", "年增")),
    "QoQ": ("季增率", "與上一季比較的變動幅度，可能受季節性影響。", "確認是否已做季節調整。", ("QoQ", "quarter-over-quarter", "季增")),
    "Share Buyback": ("股票回購／庫藏股", "公司買回自身股票，可能影響流通股數與每股盈餘，但不保證股價上漲。", "查看授權金額、實際執行及資金來源。", ("share buyback", "stock repurchase", "stock buyback", "庫藏股", "股票回購")),
    "Dividend": ("股利／配息", "公司分配獲利或現金給股東；除息與可持續性都很重要。", "確認殖利率、除息日、現金流及是否特別股利。", ("dividend", "配息", "股利")),
    "CPI": ("消費者物價指數", "衡量一籃子消費品與服務價格變動，常用於觀察通膨。", "比較公布值與市場預期，並分辨核心 CPI、月增及年增。", ("CPI", "consumer price index", "消費者物價指數")),
    "PCE": ("個人消費支出物價指數", "美國聯準會密切關注的通膨衡量指標之一。", "注意核心 PCE、實際值與預期差距。", ("PCE", "personal consumption expenditures", "個人消費支出物價")),
    "FOMC / Fed": ("聯準會／貨幣政策會議", "美國貨幣政策的決策與溝通，市場也會觀察聲明、點陣圖與主席談話。", "確認政策決定是否已公布、利率與市場原先預期的差距。", ("FOMC", "Federal Reserve", "the Fed", "聯準會", "聯邦公開市場委員會")),
    "Rate Cut / Hike": ("降息／升息", "央行調降或調升政策利率；資產影響取決於預期與經濟背景。", "確認幅度、時間與是否已反映在市場價格。", ("rate cut", "cuts rates", "cut rates", "interest rate hike", "raises rates", "hikes rates", "降息", "升息")),
    "GDP": ("國內生產毛額", "衡量某段時間內國內最終財貨與服務產出。", "確認實質或名目、季增年率以及修正值。", ("GDP", "gross domestic product", "國內生產毛額")),
    "NFP": ("非農就業人數", "美國非農部門就業變化，常與薪資及失業率一起觀察。", "核對市場預期、前期修正及薪資增幅。", ("NFP", "nonfarm payrolls", "non-farm payroll", "非農就業")),
    "Unemployment": ("失業率", "勞動人口中未就業且尋找工作者的比例。", "和勞動參與率、就業人數一起解讀。", ("unemployment rate", "失業率")),
    "Treasury Yield": ("美國公債殖利率", "美國政府債券的市場報酬率；其變動可能影響資產折現率與估值。", "區分 2 年期與 10 年期，並確認變動是否來自通膨或成長預期。", ("treasury yield", "bond yields", "10-year yield", "公債殖利率", "美債殖利率")),
    "ETF": ("指數股票型基金", "在交易所買賣的基金，依標的不同可能追蹤股票、債券或加密資產。", "確認追蹤標的、基金費用與是否為現貨型產品。", ("ETF", "exchange-traded fund", "指數股票型基金")),
    "Spot ETF": ("現貨型 ETF", "以實際現貨資產或相應安排追蹤價格的 ETF 類型；結構須依產品文件核實。", "查看官方申請／核准文件、資金流向與風險揭露。", ("spot ETF", "spot bitcoin etf", "現貨 ETF", "現貨型 ETF")),
    "SEC": ("美國證券交易委員會", "監管美國證券市場的重要機關，其公告需核對官方原文。", "確認申請、裁決、正式核准或僅為傳聞。", ("SEC", "Securities and Exchange Commission", "美國證券交易委員會")),
    "Liquidation": ("強制平倉", "槓桿部位保證金不足時被強制結清，可能加劇市場短期波動。", "檢查數據來源、統計時間與多空部位分布。", ("liquidations", "liquidation", "爆倉", "強制平倉")),
    "Funding Rate": ("永續合約資金費率", "多空永續合約持倉方定期支付的費用，可反映部分市場部位偏向。", "確認交易所、費率計算頻率和極端行情。", ("funding rate", "資金費率")),
    "Halving": ("比特幣減半", "比特幣區塊補貼定期減少的協議機制；價格效果不能單靠供給事件判斷。", "確認鏈上高度、供給變化及同期需求。", ("halving", "減半")),
    "Tariff": ("關稅", "對跨境商品徵收的稅費，可能影響供應鏈、終端價格與企業利潤。", "確認適用國家、品項、生效日期及豁免條件。", ("tariff", "tariffs", "關稅")),
    "Export Controls": ("出口管制", "對部分技術、產品或交易進行限制，可能影響企業市場與供應鏈。", "確認正式法規、產品範圍與生效時間。", ("export controls", "export restrictions", "出口管制")),
}

# Category descriptions are conditional hypotheses, NOT conclusions from headline-only data.
EVENT_RULES = (
    {
        "name": "企業財報與財測",
        "patterns": ("earnings", "quarterly results", "profit forecast", "guidance", "reports revenue",
                     "eps", "profits", "財報", "營收", "財測", "毛利率"),
        "channel": "公司營收、利潤率、未來財測與市場原先預期的差距。",
        "possible": "若實績或財測優於市場先前預期，可能支持估值；若低於預期，則可能造成壓力。即使優於預期也可能因利多出盡而下跌。",
        "verify": ("核對公告中的實際營收、EPS 和財測數字。", "比較公告前市場共識值與股價已反映的預期。"),
    },
    {
        "name": "利率與央行政策",
        "patterns": ("fomc", "federal reserve", "the fed", "rate cut", "rate hike", "interest rates", "央行", "聯準會", "降息", "升息"),
        "channel": "無風險利率、折現率、美元、資金成本與風險偏好。",
        "possible": "政策比市場原先預期更寬鬆時，部分風險資產可能受惠；但若降息反映衰退風險，市場反應也可能相反。",
        "verify": ("確認正式政策、利率幅度與發布時間。", "查看市場事前預期、債券殖利率與美元的同步反應。"),
    },
    {
        "name": "通膨與物價",
        "patterns": ("inflation", "cpi", "pce", "consumer prices", "通膨", "物價指數", "物價上漲"),
        "channel": "利率預期、企業成本與消費者購買力。",
        "possible": "通膨低於預期可能緩解部分升息壓力；高於預期則可能推升殖利率，但仍須看經濟成長與市場事前定價。",
        "verify": ("比較實際公布值、預估值、前值及修正值。", "區分核心和整體、年增和月增。"),
    },
    {
        "name": "就業與經濟成長",
        "patterns": ("nonfarm", "payrolls", "unemployment", "jobs report", "gdp", "jobless", "非農", "失業率", "經濟成長", "國內生產毛額"),
        "channel": "景氣展望、消費能力與貨幣政策預期。",
        "possible": "就業或成長較強可能支持企業營收，也可能降低降息機率；疲弱數據同時有利率利多與景氣利空兩面。",
        "verify": ("核對實際值、共識預期與修正值。", "檢查失業率、薪資與勞動參與率。"),
    },
    {
        "name": "加密貨幣政策與市場結構",
        "patterns": ("bitcoin", "ethereum", "crypto", "blockchain", "sec", "spot etf", "liquidation",
                     "funding rate", "halving", "比特幣", "以太幣", "加密", "爆倉", "資金費率"),
        "channel": "監管、ETF 需求、槓桿部位與市場流動性。",
        "possible": "政策或資金流向的變化可能影響波動，但價格方向取決於實際內容、先前預期與槓桿清算。",
        "verify": ("核對交易所、監管單位或基金的原始公告。", "區分 ETF 資金流、價格漲跌與清算量，避免混為因果。"),
    },
    {
        "name": "貿易、供應鏈與地緣政策",
        "patterns": ("tariff", "export control", "trade restrictions", "sanctions", "geopolit",
                     "關稅", "出口管制", "制裁", "地緣政治"),
        "channel": "跨國營收、供應鏈成本、銷售限制與市場風險偏好。",
        "possible": "限制可能提高相關企業成本或影響客戶需求；但替代供應商與競爭企業也可能出現不同效果。",
        "verify": ("確認政策是否正式發布及生效時間。", "辨別受影響國家、產業、公司和產品範圍。"),
    },
    {
        "name": "股利、回購與資本政策",
        "patterns": ("dividend", "buyback", "repurchase", "special dividend", "庫藏股", "股利", "配息", "股票回購"),
        "channel": "股東回報、流通股數、現金流與公司資本配置。",
        "possible": "回購或配息可能改善部分投資人預期，但同時會消耗現金，且市場也可能已先行反映。",
        "verify": ("確認董事會決議、實際金額與執行期間。", "評估公司現金流、負債與資本支出需求。"),
    },
)

GENERAL_CAVEATS = (
    "只根據新聞標題與可見的來源資訊整理，沒有核對報導全文或企業原始財報。",
    "正向／負向情境是條件推演，不代表新聞已證實，也不是價格預測或交易建議。",
    "新聞發布時間不等於市場開始反應的時間；可能有提前預期、延遲報導或其他同時發生的事件。",
)

def _matches(text, aliases):
    lowered = text.casefold()
    for raw in aliases:
        alias=raw.casefold()
        escaped=re.escape(alias)
        # Avoid 'CPI' matching unrelated English word fragments.
        if alias[0].isascii() and alias[0].isalnum():
            escaped=r"(?<![a-z0-9])"+escaped
        if alias[-1].isascii() and alias[-1].isalnum():
            escaped=escaped+r"(?![a-z0-9])"
        if re.search(escaped, lowered):
            return True
    return False

def lookup_terms(query="",limit=80):
    """Search by English name or Chinese definition without online requests."""
    q=str(query or "").strip().casefold()
    rows=[]
    for english,(chinese,meaning,verify,aliases) in TERMS.items():
        haystack=" ".join((english,chinese,meaning,*aliases)).casefold()
        if not q or q in haystack:
            rows.append({"english":english,"chinese":chinese,"meaning":meaning,"verify":verify})
    return rows[:limit]

def matched_terms(headline,limit=8):
    result=[]
    for english,(chinese,meaning,verify,aliases) in TERMS.items():
        if _matches(headline,aliases):
            result.append({"english":english,"chinese":chinese,"meaning":meaning,"verify":verify})
        if len(result)>=limit:
            break
    return result

def source_context(source):
    name=str(source or "").strip()
    if name == "Federal Reserve":
        return "聯準會官方 RSS 來源；仍需打開官方公告確認完整內容。"
    if "Google News" in name:
        return "Google News 是新聞索引，不是原始發布機構；請打開連結查核原媒體或官方資料。"
    if name in {"CNBC Markets","CoinDesk"}:
        return "媒體新聞來源，不等於企業或政府正式公告；重要數字應回查原始資料。"
    if not name or name=="使用者輸入":
        return "使用者貼上的標題：尚未提供可驗證的新聞來源。"
    return "目前未驗證此來源的發布者身分；請自行核對原始連結。"

def analyze_headline(headline,source=None,limit_events=3):
    """Generate traceable conditional explanations; make zero market predictions."""
    text=str(headline or "").strip()[:600]
    if not text:
        return {"headline":"","events":[],"terms":[],"source_note":source_context(source),
                "caveats":GENERAL_CAVEATS,"unclassified":True}
    matches=[rule for rule in EVENT_RULES if _matches(text,rule["patterns"])][:limit_events]
    events=[{"name":rule["name"],"channel":rule["channel"],
             "possible":rule["possible"],"verify":rule["verify"]} for rule in matches]
    return {"headline":text,"events":events,"terms":matched_terms(text),
            "source_note":source_context(source),
            "caveats":GENERAL_CAVEATS,"unclassified":not bool(events)}
