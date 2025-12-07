import os
import requests


# You will set these in your backend environment (.env or hosting env vars)
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "sandbox")  # "sandbox" or "live"


if PAYPAL_ENV == "live":
    PAYPAL_BASE_URL = "https://api-m.paypal.com"
else:
    # default: sandbox
    PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


def _get_access_token() -> str:
    """
    Get OAuth2 access token from PayPal.
    """
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise RuntimeError("PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not set")

    token_url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"

    # PayPal uses Basic Auth with client_id:client_secret
    resp = requests.post(
        token_url,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"]


def create_paypal_order(total_amount: str, currency: str = "USD") -> dict:
    """
    Create a PayPal order and return {id, approval_url}.
    total_amount should be a string like "10.00".
    """
    access_token = _get_access_token()

    orders_url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": total_amount,
                }
            }
        ],
    }

    resp = requests.post(orders_url, headers=headers, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    approval_url = None
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    return {
        "id": data.get("id"),
        "approval_url": approval_url,
        "raw": data,
    }
