# backend/notifications.py
import os
import smtplib
import ssl


# --- SMTP configuration ---
# For now we use Gmail + app password.
# Make sure these are set in your environment before running uvicorn.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.environ.get("CIRCLE_SMTP_USER")      # your full Gmail address
SMTP_PASSWORD = os.environ.get("CIRCLE_SMTP_PASS")  # your Gmail app password

FROM_EMAIL = SMTP_USER
FROM_NAME = "Circle"


def send_email(to_email: str, subject: str, body: str):
    """
    Send a plain-text email via Gmail SMTP with TLS.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        # Fail loudly so you see it in the terminal
        print("❌ SMTP is not configured (CIRCLE_SMTP_USER / CIRCLE_SMTP_PASS missing).")
        return

    msg = f"From: {FROM_NAME} <{FROM_EMAIL}>\r\n" \
          f"To: {to_email}\r\n" \
          f"Subject: {subject}\r\n" \
          f"Content-Type: text/plain; charset=utf-8\r\n" \
          "\r\n" \
          f"{body}"

    print("=== EMAIL OUT (attempting real send) ===")
    print(f"From: {FROM_NAME} <{FROM_EMAIL}>")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    # don't print full body every time in case it's long
    print("=== END EMAIL HEADER ===")

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg)

    print("✅ Email sent successfully.")
