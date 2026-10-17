"""UI naming and opt-in headline translation tests (no external network)."""
import io
import json
from unittest.mock import patch

from localization.assets import asset_label, market_label
from news.translation import needs_translation, translate_headline


def test_chinese_names_keep_original_tickers():
    assert asset_label("BTC/USDT") == "比特幣（BTC/USDT）"
    assert asset_label("NVDA") == "輝達（NVDA）"
    assert asset_label("TSLA") == "特斯拉（TSLA）"
    assert asset_label("AAPL") == "蘋果（AAPL）"
    assert asset_label("SPY").endswith("（SPY）")
    assert market_label("Crypto") == "加密貨幣"
    assert asset_label("UNSUPPORTED") == "UNSUPPORTED"


def test_news_translation_language_detection():
    assert needs_translation("Federal Reserve raises interest rates")
    assert not needs_translation("比特幣創新高 Bitcoin BTC")
    assert not needs_translation("2026-10-17")
    assert translate_headline("台積電營收成長") == ("台積電營收成長", False)


def test_translation_success_without_network():
    response = io.BytesIO(json.dumps({
        "responseStatus": 200,
        "responseData": {"translatedText": "聯準會宣布降息"},
    }).encode("utf-8"))
    with patch("news.translation.urllib.request.urlopen", return_value=response) as opener:
        translation, ok = translate_headline("Federal Reserve cuts interest rates")
    assert translation == "聯準會宣布降息"
    assert ok
    url = opener.call_args.args[0].full_url
    assert "langpair=en%7Czh-TW" in url


def test_translation_failure_falls_back_to_original():
    with patch("news.translation.urllib.request.urlopen", side_effect=TimeoutError):
        assert translate_headline("Crypto market changes") == ("Crypto market changes", False)
