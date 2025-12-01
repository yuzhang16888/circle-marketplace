# backend/notifications.py
import os
import smtplib
import ssl
from email.message import EmailMessage

# --- SMTP configuration ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.environ.get("CIRCLE_SMTP_USER")      # e.g. jo@circlemarketplace.club
SMTP_PASSWORD = os.environ.get("CIRCLE_SMTP_PASS")  # app password

FROM_EMAIL = SMTP_USER
FROM_NAME = "Circle"


def send_email(to_email: str, subject: str, body: str):
    """
    Send a UTF-8 plain-text email via Gmail SMTP with TLS.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("❌ SMTP is not configured (CIRCLE_SMTP_USER / CIRCLE_SMTP_PASS missing).")
        return

    # Build a proper email message with UTF-8
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body, subtype="plain", charset="utf-8")

    print("=== EMAIL OUT (attempting real send) ===")
    print(f"From: {msg['From']}")
    print(f"To: {msg['To']}")
    print(f"Subject: {msg['Subject']}")
    print("=== END EMAIL HEADER ===")

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    print("✅ Email sent successfully.")
