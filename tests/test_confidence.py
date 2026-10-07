import pandas as pd
from analytics.confidence import confidence_from_challenge, combined_signal

def test_confidence_reads_checks():
    result={"score":83,"checks":pd.DataFrame([
        {"挑戰":"Walk-Forward","結果":"PASS","說明":"4/5 區段通過"},
        {"挑戰":"牛熊盤整","結果":"WATCH","說明":"1/3 種環境為正"}
    ])}
    score,label,reasons,cautions=confidence_from_challenge(result)
    assert score==83
    assert len(reasons)==1 and len(cautions)==1

def test_combined_signal_high():
    total,verdict,explanation=combined_signal(90,85)
    assert total>=80
    assert verdict=="高優先觀察"

def test_combined_signal_warns_when_history_weak():
    total,verdict,explanation=combined_signal(80,40)
    assert "可信度不足" in verdict
