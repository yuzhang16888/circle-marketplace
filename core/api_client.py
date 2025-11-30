# core/api_client.py
import os
import requests
from typing import Optional

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BACKEND_BASE_URL}{path}"


# --------- Health checks ---------
def backend_ping():
    try:
        r = requests.get(_url("/ping"), timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def backend_db_ping():
    try:
        r = requests.get(_url("/db/ping"), timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


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
