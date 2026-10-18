"""Deterministic company news tests, without network requests."""
from datetime import datetime,timezone
from io import BytesIO
from unittest.mock import patch

import pytest

from news.company_feed import company_rss_url, fetch_company_news


def test_curated_company_urls_are_explicit_and_traditional_chinese():
    url=company_rss_url("nvda")
    assert "news.google.com/rss/search?" in url
    assert "zh-TW" in url
    assert "NVDA" in url
    assert "OR" in url
    assert "ceid=TW%3Azh-Hant" in url


@pytest.mark.parametrize("bad",["BTC/USDT","SPY","2330.TW","INVALID"])
def test_disallow_unsupported_symbols(bad):
    with pytest.raises(ValueError):
        company_rss_url(bad)


def test_company_news_parses_titles_and_preserves_origin():
    rss=b"""<rss><channel><item>
      <title>Nvidia beats forecasts</title>
      <link>https://example.org/news/nvda</link>
      <pubDate>Sat, 17 Oct 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""
    with patch("news.company_feed.urlopen",return_value=BytesIO(rss)):
        items,errors=fetch_company_news("NVDA")
    assert not errors
    assert len(items)==1
    assert items[0]["title"]=="Nvidia beats forecasts"
    assert items[0]["source"]=="Google News 公司新聞索引"
    assert items[0]["published"]==datetime(2026,10,17,10,0,tzinfo=timezone.utc)


def test_network_failure_does_not_break_financials():
    with patch("news.company_feed.urlopen",side_effect=TimeoutError):
        items,errors=fetch_company_news("AAPL")
    assert items==[]
    assert len(errors)==1
