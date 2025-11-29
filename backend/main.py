# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback
from backend.db import get_users_count  # 👈 new import

app = FastAPI(title="Circle Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/db/ping")
def db_ping():
    """
    Test that the backend can talk to Supabase Postgres.
    Returns users_count so we know queries are working.
    """
    try:
        count = get_users_count()
        return {"status": "ok", "users_count": count}
    except Exception as e:
        # TEMP: show full error detail so we can debug
        print("DB error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))