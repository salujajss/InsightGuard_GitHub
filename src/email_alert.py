import resend
import streamlit as st


def send_email_alert(api_key: str, to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Send an email via the Resend API.
    Returns (success: bool, error_message: str).
    No sender password needed — just the Resend API key.
    """
    if not api_key or not to_email:
        return False, "Missing API key or recipient email."
    try:
        resend.api_key = api_key
        result = resend.Emails.send({
            "from": "InsightGuard <onboarding@resend.dev>",
            "to":   [to_email],
            "subject": subject,
            "text": body,
        })
        # Resend returns an object with an 'id' on success
        if hasattr(result, "id") and result.id:
            return True, ""
        # Some versions return a dict
        if isinstance(result, dict) and result.get("id"):
            return True, ""
        return False, f"Unexpected response: {result}"
    except Exception as e:
        return False, str(e)
