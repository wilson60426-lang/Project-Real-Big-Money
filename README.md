# Project Real Big Money

加密貨幣策略研究與回測工具。

## v0.6 — Trade Engine

v0.6 將回測從 K 線層級提升到「完整交易」層級。

### 新增
- 完整進場 → 持有 → 出場 Trade Engine
- 真正逐筆交易勝率
- 平均獲利 / 平均虧損
- Payoff Ratio
- 每筆 Expectancy
- Profit Factor（逐筆）
- 最大連續虧損
- 平均持倉 K 線數
- MAE / MFE
- 固定滑價假設
- 完整交易紀錄表
- 新手白話解釋

### 注意
目前滑價仍是固定假設，不代表真實成交品質。
目前歷史資料介面最多 1000 根 K 線，因此尚不足以取代多年期穩健性測試。
MAE/MFE 可用於後續研究停損停利，但不應直接用歷史最佳值設定參數。

## Windows
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501`。

本專案僅供研究，不構成投資建議；歷史績效不代表未來績效。
