# backend/notifications.py
import os
import smtplib
import ssl
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str):
    """
    Send an email using SMTP.
    For production, configure via environment variables:

      SMTP_HOST      (e.g. smtp.gmail.com)
      SMTP_PORT      (e.g. 465)
      SMTP_USER      (your login, e.g. your Gmail address)
      SMTP_PASSWORD  (your SMTP password or Gmail app password)
      EMAIL_FROM     (optional, display From; defaults to SMTP_USER)

    If config is missing, this will just print the email contents.
    """

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port_str = os.getenv("SMTP_PORT", "465")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("EMAIL_FROM", smtp_user if smtp_user else "no-reply@example.com")

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 465

    # Debug print – always
    print("=== EMAIL OUT (attempting real send) ===")
    print(f"To: {to_email}")
    print(f"From: {from_email}")
    print(f"Subject: {subject}")
    print("Body:")
    print(body)
    print("=== END EMAIL ===")

    # If we don't have credentials, don't crash – just return after printing
    if not smtp_user or not smtp_password:
        print("EMAIL SEND SKIPPED: SMTP_USER or SMTP_PASSWORD not set.")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        context = ssl.create_default_context()

        # Using SSL (port 465); for STARTTLS you'd use SMTP + starttls
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"EMAIL SENT SUCCESSFULLY to {to_email}")

    except Exception as e:
        print(f"EMAIL SEND ERROR: {e}")
