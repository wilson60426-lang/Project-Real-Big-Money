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
    distance=current_price/target_price-1
    if direction=="below":
        hit=current_price<=target_price
        msg="已進入你的觀察價以下" if hit else f"距離觀察價還有 {abs(distance):.2%}"
    else:
        hit=current_price>=target_price
        msg="已突破你的觀察價" if hit else f"距離觀察價還有 {abs(distance):.2%}"
    return AlertResult(hit,"TRIGGERED" if hit else "WATCH",msg,float(distance))

def entry_score(price_hit: bool, signal: int=0, rsi: float|None=None, challenge_score: int|None=None, trend_up: bool|None=None):
    score=40 if price_hit else 0
    reasons=[]
    cautions=[]
    if price_hit: reasons.append("價格條件達標")
    else: cautions.append("價格尚未進入設定的觀察區")
    if signal==1:
        score+=20; reasons.append("策略目前為多方訊號")
    elif signal<0:
        cautions.append("策略目前偏空")
    if rsi is not None:
        if 25<=rsi<=45:
            score+=15; reasons.append("RSI 位於偏低觀察區")
        elif rsi>=70:
            cautions.append("RSI 偏高，注意追價風險")
    if trend_up is True:
        score+=10; reasons.append("短期均線位於長期均線上方")
    elif trend_up is False:
        cautions.append("趨勢尚未轉強")
    if challenge_score is not None:
        if challenge_score>=80:
            score+=15; reasons.append("策略 Challenge 驗證較強")
        elif challenge_score>=60:
            score+=8; reasons.append("策略 Challenge 驗證為觀察")
        else:
            cautions.append("策略 Challenge 驗證偏弱")
    score=min(100,score)
    label="高優先觀察" if score>=80 else "候選觀察區" if score>=60 else "持續觀察" if score>=40 else "條件不足"
    return score,label,reasons,cautions
