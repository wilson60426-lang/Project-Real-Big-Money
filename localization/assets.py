"""PRBM Traditional Chinese display names.

Ticker symbols always remain unchanged in market requests and backtests.
"""

ASSET_NAMES_ZH = {
    "BTC": "比特幣",
    "BTC/USDT": "比特幣",
    "ETH": "以太幣",
    "ETH/USDT": "以太幣",
    "SOL": "索拉納",
    "SOL/USDT": "索拉納",
    "USDT": "泰達幣",
    "AAPL": "蘋果",
    "MSFT": "微軟",
    "NVDA": "輝達",
    "AMZN": "亞馬遜",
    "GOOGL": "Alphabet（Google 母公司）",
    "META": "Meta（臉書母公司）",
    "TSLA": "特斯拉",
    "SPY": "SPDR 標普 500 ETF",
    "QQQ": "Invesco 納斯達克 100 ETF",
    "IWM": "iShares 羅素 2000 ETF",
    "2330.TW": "台積電",
    "0050.TW": "元大台灣 50 ETF",
    "2317.TW": "鴻海",
    "2454.TW": "聯發科",
}

MARKET_NAMES_ZH = {"Crypto": "加密貨幣", "Equity": "美股", "美股": "美股", "台股": "台股"}

def asset_label(symbol: str) -> str:
    """Return bilingual UI label, or raw ticker for unrecognized assets."""
    ticker = str(symbol).strip()
    name = ASSET_NAMES_ZH.get(ticker.upper())
    return f"{name}（{ticker}）" if name else ticker

def market_label(market: str) -> str:
    return MARKET_NAMES_ZH.get(market, market)
