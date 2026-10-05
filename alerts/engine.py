from dataclasses import dataclass

@dataclass
class AlertResult:
    triggered: bool
    status: str
    message: str
    distance_pct: float

def evaluate_price_alert(current_price: float, target_price: float, direction: str="below") -> AlertResult:
    if current_price <= 0 or target_price <= 0:
        return AlertResult(False,"ERROR","價格必須大於 0。",0.0)
    distance=(current_price/target_price-1)
    if direction=="below":
        hit=current_price<=target_price
        msg="已進入你的觀察價以下" if hit else f"距離觀察價還有 {abs(distance):.2%}"
    else:
        hit=current_price>=target_price
        msg="已突破你的觀察價" if hit else f"距離觀察價還有 {abs(distance):.2%}"
    return AlertResult(hit,"TRIGGERED" if hit else "WATCH",msg,float(distance))

def entry_score(price_hit: bool, signal: int=0, rsi: float|None=None, challenge_score: int|None=None):
    score=40 if price_hit else 0
    reasons=[]
    if price_hit: reasons.append("價格條件達標")
    if signal==1: score+=25; reasons.append("策略目前為多方訊號")
    if rsi is not None and 25<=rsi<=45: score+=15; reasons.append("RSI 位於偏低但非極端區")
    if challenge_score is not None:
        if challenge_score>=80: score+=20; reasons.append("策略挑戰驗證較強")
        elif challenge_score>=60: score+=10; reasons.append("策略挑戰驗證為觀察")
    score=min(100,score)
    label="候選觀察區" if score>=70 else "持續觀察" if score>=40 else "條件不足"
    return score,label,reasons
