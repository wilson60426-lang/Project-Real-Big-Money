import os
import smtplib
from email.message import EmailMessage

def gmail_configured():
    return bool(
        os.getenv("GMAIL_ADDRESS","").strip()
        and os.getenv("GMAIL_APP_PASSWORD","").strip()
        and os.getenv("ALERT_EMAIL_TO","").strip()
    )

def send_gmail(subject: str, message: str):
    sender=os.getenv("GMAIL_ADDRESS","").strip()
    password=os.getenv("GMAIL_APP_PASSWORD","").replace(" ","").strip()
    recipient=os.getenv("ALERT_EMAIL_TO","").strip()
    if not sender or not password or not recipient:
        return False,"尚未設定 GMAIL_ADDRESS / GMAIL_APP_PASSWORD / ALERT_EMAIL_TO"

    mail=EmailMessage()
    mail["From"]=sender
    mail["To"]=recipient
    mail["Subject"]=subject
    mail.set_content(message)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465,timeout=20) as smtp:
            smtp.login(sender,password)
            smtp.send_message(mail)
        return True,"Gmail 提醒已寄出"
    except Exception as e:
        return False,"Gmail 發送失敗："+str(e)
