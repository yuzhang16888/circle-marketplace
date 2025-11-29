# core/api_client.py
import requests
import streamlit as st  # so we can show debug info in the sidebar

API_BASE_URL = "http://localhost:8000"  # keep it hardcoded for now

def backend_ping() -> bool:
    """Return True if backend /ping says it's alive. Show error if not."""
    url = f"{API_BASE_URL}/ping"
    try:
        resp = requests.get(url, timeout=3)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("status") == "ok"
        if not ok:
            st.sidebar.write(f"Ping failed: status={resp.status_code}, body={data}")
        return ok
    except Exception as e:
        st.sidebar.write(f"Ping error: {e}")
        return False

def backend_db_ping() -> bool:
    """Return True if /db/ping can reach Supabase and show user count."""
    url = f"{API_BASE_URL}/db/ping"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("status") == "ok"
        if ok:
            users_count = data.get("users_count", 0)
            st.sidebar.write(f"DB users_count: {users_count}")
        else:
            st.sidebar.write(f"DB ping failed: status={resp.status_code}, body={data}")
        return ok
    except Exception as e:
        st.sidebar.write(f"DB ping error: {e}")
        return False