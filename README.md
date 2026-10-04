# Project Real Big Money

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
