# Project Real Big Money

加密貨幣策略研究與回測工具。

## v0.5 — 新手介面 + 回測品質中心

v0.5 的目標不是增加更多看不懂的數字，而是回答：
1. 過去有沒有賺？
2. 中間可能承受多大回撤？
3. 這份回測有多值得相信？
4. 下一步應該繼續研究還是淘汰？

### 新增
- 🌱 新手模式 / 🔬 專業模式
- Backtest Quality Score（0–100）
- 資料量評分
- 交易樣本評分
- 風險控制評分
- 風險調整績效評分
- 獲利品質評分
- 70/30 樣本外驗證評分
- 10 萬元最大回撤白話換算
- 每個品質項目的中文解釋
- 下一步研究建議
- 明確區分「值得研究」與「買入訊號」

### 仍保留
- BTC / ETH / SOL
- 15m / 1h / 4h / 1d
- SMA Cross / RSI Reversion / Trend + RSI
- Sharpe / Sortino / Profit Factor
- 最大回撤
- Strategy vs Buy & Hold

## Windows

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501`。

## 目前限制
v0.5 的 Quality Score 是研究輔助評分，不是獲利機率。交易勝率目前仍以持倉期間正報酬 K 線近似，下一階段應建立完整 Trade Engine，才能計算真正逐筆交易勝率、平均盈虧、MAE/MFE、連敗與 Expectancy。

本專案僅供研究，不構成投資建議；歷史績效不代表未來績效。
