import os
from dotenv import load_dotenv

load_dotenv()
EXCHANGE = os.getenv("EXCHANGE", "binance")
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
TIMEFRAME = "1h"
STARTING_CAPITAL = 100_000.0
FEE_RATE = 0.001
MAX_POSITION_PCT = 0.10
