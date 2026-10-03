from config.settings import EXCHANGE, SYMBOLS, TIMEFRAME, FEE_RATE
from data.market_data import fetch_ohlcv
from indicators.basic import add_indicators
from strategies.sma_cross import generate_signals
from backtesting.engine import backtest


def main():
    for symbol in SYMBOLS:
        df = fetch_ohlcv(EXCHANGE, symbol, TIMEFRAME)
        df = add_indicators(df)
        df = generate_signals(df)
        print(symbol, backtest(df, FEE_RATE))


if __name__ == "__main__":
    main()
