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
