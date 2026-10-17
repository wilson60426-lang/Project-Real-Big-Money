"""Offline regression tests for bilingual financial research explanations."""
from news.research_assistant import analyze_headline, lookup_terms, matched_terms, source_context


def test_earnings_and_guidance_are_explained_without_price_prediction():
    report=analyze_headline("Nvidia beats earnings estimates but lowers revenue guidance",
                            source="CNBC Markets")
    assert not report["unclassified"]
    assert any(event["name"]=="企業財報與財測" for event in report["events"])
    names={term["english"] for term in report["terms"]}
    assert "Revenue" in names
    assert "Guidance" in names
    assert "Earnings" in names
    assert "媒體" in report["source_note"]
    assert all(event["verify"] for event in report["events"])
    assert all("買進" not in event["possible"] for event in report["events"])


def test_cpi_fed_events_are_conditional():
    report=analyze_headline("Fed weighs CPI inflation as interest rates remain high")
    names={event["name"] for event in report["events"]}
    assert "利率與央行政策" in names
    assert "通膨與物價" in names
    assert len(report["events"])<=3
    assert any(term["english"]=="CPI" for term in report["terms"])


def test_chinese_terms_and_glossary_search():
    report=analyze_headline("聯準會降息與台灣企業營收及毛利率")
    assert not report["unclassified"]
    assert any(x["chinese"]=="毛利率" for x in report["terms"])
    assert any(row["english"]=="EPS" for row in lookup_terms("每股盈餘"))
    assert any(row["english"]=="FCF" for row in lookup_terms("自由現金流"))
    assert lookup_terms("不存在的隨機詞彙xyz")==[]


def test_unknown_or_empty_titles_do_not_invent_causality():
    for title in ("", "Blue chairs on sale", "UNKNOWN123"):
        report=analyze_headline(title)
        assert report["unclassified"]
        assert report["events"]==[]
        assert len(report["caveats"])>=2


def test_english_abbreviation_does_not_match_word_fragment():
    assert not any(term["english"]=="CPI" for term in matched_terms("SCPIX revenue"))
    assert any(term["english"]=="CPI" for term in matched_terms("CPI inflation rises"))


def test_rss_source_provenance_is_not_overstated():
    assert "索引" in source_context("Google News 美股（繁中）")
    assert "官方" in source_context("Federal Reserve")
    assert "尚未提供" in source_context("使用者輸入")


def test_long_headline_is_bounded_for_display():
    report=analyze_headline("CPI " * 1000)
    assert len(report["headline"])==600
