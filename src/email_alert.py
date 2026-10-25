import smtplib
from email.message import EmailMessage

def send_email_alert(sender,password,receiver,subject,body):
    if not sender or not password or not receiver:
        print("Email configuration incomplete; alert not sent.")
        return False
    try:
        msg=EmailMessage(); msg["From"]=sender; msg["To"]=receiver; msg["Subject"]=subject; msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,password); server.send_message(msg)
        print("Email alert sent successfully."); return True
    except Exception as e:
        print(f"Email could not be sent: {e}"); return False
