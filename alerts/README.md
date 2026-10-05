# Entry Alert Engine

目前 v0.9.2 先建立「觀察提醒」邏輯，不自動下單。

## 原則
- 價格到達 ≠ 一定該買。
- 系統使用「候選觀察區」而不是「保證買點」。
- Entry Score 可結合價格、策略訊號、RSI 與 Challenge Score。
- 下一階段才接 Telegram / Email 等背景通知。
- 必須加入 cooldown 與去重複通知，避免門檻附近重複轟炸。

這個模組刻意與 Streamlit UI 分離，未來可由背景排程器重複呼叫。
