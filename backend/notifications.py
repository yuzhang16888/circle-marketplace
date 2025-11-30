# backend/notifications.py

# backend/notifications.py

def send_email(to_email: str, subject: str, body: str):
    """
    Placeholder email sender for MVP.
    For now just print to console. Later we can integrate real SMTP / SendGrid / Mailgun.
    """
    print("=== EMAIL OUT ===")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("Body:")
    print(body)
    print("=== END EMAIL ===")

