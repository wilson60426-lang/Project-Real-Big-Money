# Project Real Big Money

## v0.9 — Challenge & Validation Engine

核心原則：**不要只證明策略有效，要主動嘗試證明它無效。**

### 新增
- Strategy Challenge Engine
- Bootstrap 交易重抽樣與 Expectancy 90% 區間
- Bootstrap 正期望比例
- Monte Carlo 回撤壓力測試
- 跨年份、牛熊盤整、Walk-Forward 驗證
- 3 倍交易成本壓力
- PASS / WATCH / FAIL Challenge Score
- challenge_app.py 獨立介面
- pytest 核心測試
- GitHub Actions CI：push / pull request 自動測試

### 執行
主跨資產介面：
    streamlit run app.py

策略挑戰：
    streamlit run challenge_app.py

本機測試：
    pytest -q

### 尚未完成
Deflated Sharpe Ratio、Parameter Stability Heatmap、策略/參數搜尋次數追蹤、Multiple-testing correction、更嚴格的 block bootstrap，以及美股 Challenge Engine 整合。

因此 Challenge Score 是研究輔助分數，不是成功機率或投資建議。
