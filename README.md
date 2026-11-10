# Project Real Big Money

## v0.9.14｜繁體中文金融研究平台

Windows CMD 在**包含 `app.py` 的專案資料夾**執行：

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

目前主要入口包括：K 線研究室（含 Twin Range Filter）、全球金融快報、金融研究助手、美股財報研究室、市場比較、策略研究、挑戰策略、訊號可信度和價格提醒。美股與加密貨幣以繁體中文名稱加上原始英文代號顯示。

### 財報 × 新聞 × K 線研究（v0.9.13–v0.9.14）

在「🧾 美股財報研究室」可以查看可取得的營收、EPS、毛利率、歷史公布日期、當時已完成的美股日 K、公司近期公開新聞與**同期 SPY 標普 500 ETF 的價格變化**。

僅在起訖交易日能精確對齊時才計算「個股漲跌幅減去 SPY 漲跌幅（百分點）」。這是市場背景的描述性比較，**不是**風險調整超額報酬、財報造成的因果報酬、也不是交易訊號。Yahoo Finance 與免費 RSS 資料可能延遲或缺漏。

延伸說明：[財報研究](docs/earnings_research.md) · [財報消息與 K 線](docs/earnings_news_chart.md) · [同期 SPY 比較](docs/spy_market_context.md)

### 驗證

```bat
python -m pytest -q
```

請同時檢查 GitHub Actions 的最新測試結果；未確認綠勾前，不能宣稱 CI 完全通過。

---

## v0.9 Unified

現在只需要一個入口：

    streamlit run app.py

介面分成三條清楚路徑：
- 🌎 市場比較：美股 × Crypto 報酬、風險、相關性
- 🧪 策略研究：多年資料、逐筆交易、市場環境、Walk-Forward、成本壓力
- 🔥 挑戰策略：Bootstrap、Monte Carlo、跨年份與反證測試

`challenge_app.py` 暫時保留作為相容入口，但主要介面已整合到 `app.py`。

程式品質仍由 pytest 與 GitHub Actions CI 自動檢查。

### 尚未完成
Deflated Sharpe Ratio、參數穩健性熱圖、Multiple-testing correction、策略搜尋次數追蹤、block bootstrap，以及美股策略 Challenge Engine。

所有分數皆為研究輔助，不是獲利機率或投資建議。
