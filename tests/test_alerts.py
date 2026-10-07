from alerts.engine import evaluate_price_alert, entry_score

def test_below_alert_triggers():
    r=evaluate_price_alert(95,100,"below")
    assert r.triggered and r.status=="TRIGGERED"

def test_below_alert_waits():
    r=evaluate_price_alert(105,100,"below")
    assert not r.triggered and r.status=="WATCH"

def test_above_alert_triggers():
    assert evaluate_price_alert(105,100,"above").triggered

def test_entry_score_full_candidate():
    score,label,reasons,cautions=entry_score(True,1,35,85,True)
    assert score==100
    assert label=="高優先觀察"
    assert len(reasons)>=4

def test_entry_score_warns_on_weak_conditions():
    score,label,reasons,cautions=entry_score(False,-1,75,40,False)
    assert score<40
    assert len(cautions)>=3
