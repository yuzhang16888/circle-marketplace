# core/api_client.py
import os
import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def backend_ping() -> bool:
    """Return True if backend /ping says it's alive."""
    try:
        resp = requests.get(f"{API_BASE_URL}/ping", timeout=3)
        data = resp.json()
        return resp.status_code == 200 and data.get("status") == "ok"
    except Exception:
        return False
