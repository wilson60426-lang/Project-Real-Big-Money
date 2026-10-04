# Project Real Big Money

Crypto research, backtesting and paper-trading terminal.

## v0.2 — Dashboard

### Current features
- BTC / ETH / SOL
- 15m / 1h / 4h / 1d timeframes
- Historical OHLCV market data
- SMA20 / SMA50
- RSI(14)
- SMA crossover strategy
- Backtesting with configurable trading fees
- Strategy return vs Buy & Hold
- Maximum drawdown
- Position-change count
- Interactive Streamlit dashboard
- Paper-trading-first design (no live order execution)

## Run on Windows

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Your browser should open the dashboard at `http://localhost:8501`.

## Safety

This project is research software. No strategy guarantees profits. Live order execution is disabled in v0.2. Never commit exchange API keys or secrets to GitHub.

## Roadmap

v0.3 will focus on stronger performance analytics and multiple strategies. Later versions can add funding rates, open interest, liquidations, market sentiment, AI-assisted research and paper trading.
