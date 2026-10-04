# Project Real Big Money

Crypto research, backtesting and paper-trading project.

## v0.3 — Strategy Research & Validation

Current capabilities:
- BTC / ETH / SOL
- 15m / 1h / 4h / 1d
- SMA20, SMA50 and RSI14
- SMA Cross, RSI Reversion, Trend + RSI strategies
- Trading-fee-aware backtesting
- Strategy vs Buy & Hold
- Return, maximum drawdown, Sharpe, Sortino, win rate and Profit Factor
- 70/30 in-sample / out-of-sample validation
- Detailed position and return table
- No live order execution

## Windows

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501`.

## Important
This is research software, not investment advice. A profitable backtest does not imply future profitability. Never commit API keys or secrets.

## Next
v0.4: deeper market data (funding rate, open interest, long/short context), longer historical data and stronger strategy robustness testing.
