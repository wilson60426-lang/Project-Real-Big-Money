from alerts.engine import evaluate_price_alert, entry_score

def test_below_alert_triggers():
    r=evaluate_price_alert(95,100,"below")
    assert r.triggered and r.status=="TRIGGERED"

def test_below_alert_waits():
    r=evaluate_price_alert(105,100,"below")
    assert not r.triggered and r.status=="WATCH"

def test_above_alert_triggers():
    assert evaluate_price_alert(105,100,"above").triggered

def test_entry_score_bounds():
    score,label,reasons=entry_score(True,1,35,85)
    assert score==100
    assert label=="候選觀察區"
    assert len(reasons)>=3
