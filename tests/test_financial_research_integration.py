"""Static smoke tests: catch syntax regressions without loading market/network APIs."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_app_and_news_research_compile():
    for path in ("app.py","news/research_assistant.py","news/translation.py",
                 "localization/assets.py"):
        src=(ROOT/path).read_text(encoding="utf-8")
        ast.parse(src,filename=path)


def test_financial_research_is_accessible_from_both_pages():
    src=(ROOT/"app.py").read_text(encoding="utf-8")
    assert 'elif page=="📚 金融研究助手":' in src
    assert 'show_news_research(study["title"]' in src
    assert 'show_news_research(article["title"]' in src
    assert 'st.link_button("開啟原文核對 ↗",url)' in src


def test_engine_does_not_make_network_calls():
    src=(ROOT/"news/research_assistant.py").read_text(encoding="utf-8")
    assert "urllib" not in src
    assert "requests" not in src
    assert "openai" not in src.lower()


def test_earnings_kline_research_is_wired_in_and_parses():
    for path in ("analytics/earnings_reactions.py","charts/earnings_workbench.py",
                 "data/fundamentals.py","tests/test_earnings_reactions.py"):
        ast.parse((ROOT/path).read_text(encoding="utf-8"),filename=path)
    app=(ROOT/"app.py").read_text(encoding="utf-8")
    assert 'elif page=="🧾 美股財報研究室":' in app
    assert 'align_earnings_reactions(prices,eps)' in app
    assert 'make_earnings_chart(prices,eps,asset_label(symbol))' in app
    assert 'relevant_news(recent_news,symbol)' in app
    assert "新聞來自免費" not in app or "近期" in app


def test_spy_context_is_connected_and_parses():
    ast.parse((ROOT/"analytics/market_context.py").read_text(encoding="utf-8"),
              filename="analytics/market_context.py")
    ast.parse((ROOT/"tests/test_market_context.py").read_text(encoding="utf-8"),
              filename="tests/test_market_context.py")
    app=(ROOT/"app.py").read_text(encoding="utf-8")
    assert "v0.9.14" in app
    assert "fetch_spy_daily_prices()" in app
    assert "with_spy_context(observations,spy_prices)" in app
    assert "market_context_commentary(detail)" in app
