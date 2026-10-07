def confidence_from_challenge(result):
    checks=result["checks"]
    score=int(result.get("score",0))
    reasons=[]
    cautions=[]
    if checks is not None and len(checks):
        for _,row in checks.iterrows():
            name=str(row["挑戰"]); status=str(row["結果"]); detail=str(row["說明"])
            if status=="PASS":
                reasons.append(name+"：通過｜"+detail)
            elif status=="WATCH":
                cautions.append(name+"：需要觀察｜"+detail)
            else:
                cautions.append(name+"：未通過｜"+detail)
    label="歷史驗證證據較完整" if score>=80 else "有一定歷史支持" if score>=60 else "歷史證據仍不足"
    return score,label,reasons,cautions

def combined_signal(entry_score,confidence_score):
    total=round(entry_score*0.55+confidence_score*0.45)
    if entry_score>=80 and confidence_score>=80:
        verdict="高優先觀察"
        explanation="現在條件與歷史驗證同時較強，但仍不是保證獲利。"
    elif entry_score>=60 and confidence_score>=60:
        verdict="值得觀察"
        explanation="目前條件與歷史證據都有支持，可以進一步做風險評估。"
    elif entry_score>=60 and confidence_score<60:
        verdict="訊號有出現，但可信度不足"
        explanation="現在看起來有機會，但這套策略的歷史驗證還不夠穩。"
    elif entry_score<60 and confidence_score>=60:
        verdict="策略有基礎，但現在不是好時機"
        explanation="策略歷史驗證尚可，但目前進場條件沒有聚合。"
    else:
        verdict="先等待"
        explanation="目前條件與歷史證據都不足，不需要因為害怕錯過而追進。"
    return total,verdict,explanation

GLOSSARY={
    "Entry Score":"現在這一刻的條件分數。看價格、RSI、趨勢與策略訊號有沒有同時出現；不是上漲機率。",
    "Confidence Score":"這套策略過去接受壓力測試後，證據有多完整；不是未來獲利機率。",
    "RSI":"市場短期漲跌速度的『溫度計』。數字偏高代表近期漲得較急，偏低代表近期跌得較急，但不能單獨當買賣答案。",
    "SMA":"簡單移動平均線。可以想成把最近一段時間的價格取平均，用來看方向是否逐漸轉強或轉弱。",
    "Walk-Forward":"把策略拿去考『沒拿來調整策略的下一段資料』，像讀完前幾章後換新考卷，避免只會背考古題。",
    "Bootstrap":"把過去每筆交易反覆重新抽樣，看看好成績是不是只靠少數幾筆幸運交易。",
    "Monte Carlo":"把交易結果用很多種順序重排，模擬運氣較差時帳戶可能承受多大的跌幅。",
    "Max Drawdown":"最大回撤。可以理解成資金從曾經的高點往下跌，歷史上最深曾跌多少。",
    "Expectancy":"每做一筆交易，長期統計平均大約賺或虧多少。正數不代表下一筆一定賺。",
    "Slippage":"滑價。你看到的價格和真正成交價格可能有落差，回測要把這種現實成本算進去。",
    "Challenge Score":"策略撐過多少反證與壓力測試的綜合分數，不是成功率。"
}
