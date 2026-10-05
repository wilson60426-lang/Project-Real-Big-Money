# Entry Alert Engine

目前採用 Gmail 作為通知方式，不自動下單。

## 新手設定
1. 在 Google 帳號開啟兩步驟驗證。
2. 建立 Google App Password（應用程式密碼）。
3. 把專案根目錄的 .env.example 複製成 .env。
4. 在 .env 填入 GMAIL_ADDRESS、GMAIL_APP_PASSWORD、ALERT_EMAIL_TO。
5. 在 alerts/alerts.json 設定資產、價格、方向，並把 enabled 改成 true。
6. 執行 python -m alerts.monitor --once 測試一次。
7. 確認正常後執行 python -m alerts.monitor --interval 300 持續監控。

## 安全原則
- 不要使用一般 Gmail 密碼。
- 不要把 App Password 貼到 GitHub、聊天或截圖公開。
- .env 已由 .gitignore 排除。
- 價格到達 ≠ 一定該買。
- 系統使用「觀察區」而不是「保證買點」。
- 只有從未觸發變成觸發時寄信，避免重複洗信。

下一階段會把 RSI、趨勢、策略與 Challenge Score 納入 Entry Score。
