import resend


def send_email_alert(api_key: str, to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via the Resend API.
    No sender password needed — just the Resend API key.
    """
    if not api_key or not to_email:
        print("Email configuration incomplete; alert not sent.")
        return False
    try:
        resend.api_key = api_key
        resend.Emails.send({
            "from": "InsightGuard <onboarding@resend.dev>",
            "to":   [to_email],
            "subject": subject,
            "text": body,
        })
        print(f"Email alert sent to {to_email}.")
        return True
    except Exception as e:
        print(f"Email could not be sent: {e}")
        return False
