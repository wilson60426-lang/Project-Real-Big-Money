# Project Real Big Money

加密貨幣策略研究與回測工具。

## v0.4 — 繁體中文易讀介面

v0.4 將重點放在「讓非量化背景使用者也能理解結果」。

### 功能
- 繁體中文 Dashboard
- BTC / ETH / SOL
- 15m / 1h / 4h / 1d
- 均線交叉、RSI 超賣反彈、趨勢＋RSI
- 策略報酬 vs 單純持有
- 最大回撤
- Sharpe 夏普比率
- Sortino 索提諾比率
- 勝率與 Profit Factor 獲利因子
- 70/30 樣本外驗證
- 白話策略健檢與風險提示
- 進階數據可收合
- 無真實下單功能

## Windows 啟動

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501`。

## 注意
本專案僅供研究，不構成投資建議。歷史回測獲利不代表未來獲利。請勿將 API Key 或 Secret 提交至 GitHub。
