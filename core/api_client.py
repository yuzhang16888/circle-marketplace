# core/api_client.py
# import os
# import requests
# from typing import Optional

# BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
import os
import requests
import streamlit as st
from typing import Optional

# Determine backend URL in this order:
# 1) st.secrets on Streamlit Cloud
# 2) Environment variable (local dev)
# 3) Fallback to localhost
BACKEND_BASE_URL = st.secrets.get(
    "BACKEND_BASE_URL",
    os.getenv("BACKEND_BASE_URL", "http://localhost:8000"),
)


def _url(path: str) -> str:
    """
    Build a full request URL based on BACKEND_BASE_URL.

    Example:
        _url("/auth/login") -> "https://your-ngrok-url/auth/login"
    """
    # Ensure BACKEND_BASE_URL has no trailing slash
    base = BACKEND_BASE_URL.rstrip("/")
    return f"{base}{path}"



# --------- Health checks ---------
# def backend_ping():
#     try:
#         r = requests.get(_url("/ping"), timeout=3)
#         r.raise_for_status()
#         return r.json()
#     except Exception:
#         return None


# def backend_db_ping():
#     try:
#         r = requests.get(_url("/db/ping"), timeout=3)
#         r.raise_for_status()
#         return r.json()
#     except Exception:
#         return None


# --------- Auth ---------
def register_user(email: str, password: str, full_name: Optional[str] = None):
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
    }
    r = requests.post(_url("/auth/register"), json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def login_user(email: str, password: str):
    payload = {
        "email": email,
        "password": password,
    }
    r = requests.post(_url("/auth/login"), json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


# --------- Invites (for step B) ---------
from typing import Optional

def create_invite(email: str, name: Optional[str] = None, invited_by_id: Optional[int] = None):
    payload = {
        "email": email,
        "name": name,
        "invited_by_id": invited_by_id,
    }
    r = requests.post(_url("/invites/create"), json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def list_invites_by_inviter(invited_by_id: int):
    r = requests.get(_url(f"/invites/by_inviter/{invited_by_id}"), timeout=5)
    r.raise_for_status()
    return r.json()

def list_invites():
    r = requests.get(_url("/invites"), timeout=5)
    r.raise_for_status()
    return r.json()
