"""Focused US company headline search using public Google News RSS.

Titles only. Results are neither guaranteed complete nor verified against the
company's original earnings release. No paid data or article scraping.
"""
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from data.fundamentals import ALLOWED_US_STOCKS
from news.free_feed import parse_feed

COMPANY_QUERIES = {
    "AAPL": 'Apple AAPL 蘋果公司 財報',
    "MSFT": 'Microsoft MSFT 微軟 財報',
    "NVDA": 'NVIDIA NVDA 輝達 財報',
    "AMZN": 'Amazon AMZN 亞馬遜 財報',
    "GOOGL": 'Alphabet GOOGL Google 財報',
    "META": 'Meta Platforms META 財報',
    "TSLA": 'Tesla TSLA 特斯拉 財報',
}


def company_rss_url(symbol):
    ticker=str(symbol).strip().upper()
    if ticker not in ALLOWED_US_STOCKS:
        raise ValueError("目前沒有支援這個美股標的的公司新聞搜尋。")
    query=COMPANY_QUERIES[ticker]
    params=urlencode({"q":query,"hl":"zh-TW","gl":"TW","ceid":"TW:zh-Hant"})
    return "https://news.google.com/rss/search?"+params


def fetch_company_news(symbol, limit=16, timeout=7):
    """Return (RSS headline items, provider errors); do not claim completeness."""
    url=company_rss_url(symbol)
    label="Google News 公司新聞索引"
    try:
        req=Request(url,headers={"User-Agent":"Mozilla/5.0 PRBM-NewsResearch/1.0"})
        with urlopen(req,timeout=timeout) as response:
            body=response.read(1_500_000)
        articles=parse_feed(body,label,"美股")
        # The query itself is company-specific; snippets may mention peers.
        articles.sort(
            key=lambda item:item.get("published") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return articles[:max(0,min(int(limit),30))],[]
    except (OSError,ValueError,TypeError,TimeoutError):
        return [],[label+" 暫時無法讀取"]
