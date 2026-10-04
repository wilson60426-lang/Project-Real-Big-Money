# Project Real Big Money

## v0.7 — Strategy Validation Engine

Project Real Big Money 的目標不是找「回測報酬最高」的策略，而是找 **最難被證明是假的策略**。

### v0.7 新增
- 1 / 2 / 3 / 5 年歷史資料
- CCXT OHLCV 自動分頁，突破單次 1000 根 K 線限制
- 真正完整交易樣本
- 牛市 / 熊市 / 盤整拆分
- 5 段 Walk-Forward 驗證
- 1x / 1.5x / 2x / 3x 手續費與滑價壓力測試
- Strategy Validation Score 0–100
- PASS / WATCH / FAIL 新手判讀
- 新手模式與專業模式

### 重要限制
Validation Score **不是獲利機率**。
目前市場 Regime 分類屬於簡化研究版本；Walk-Forward 目前是在不同時間區段驗證固定策略，而不是完整的參數重新最佳化流程。
尚未加入 Deflated Sharpe Ratio、Monte Carlo、Bootstrap、參數穩健性熱圖與真正的策略搜尋次數追蹤。

這些限制刻意寫清楚，避免產生「假精密」。

## 執行
```bat
python -m pip install -r requirements.txt
streamlit run app.py
```

本專案僅供研究，不構成投資建議；歷史績效不代表未來績效。
