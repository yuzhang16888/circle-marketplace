# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.db import get_users_count, create_user, get_user_by_email


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



from pydantic import BaseModel
from backend.db import create_user, get_user_by_email

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None

@app.post("/auth/register")
def register(payload: RegisterRequest):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    # 1) Check if email already exists
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # 2) Create the user
    user_id = create_user(email=email, password=password, full_name=payload.full_name)
    return {"status": "ok", "user_id": user_id}



class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


@app.post("/auth/register")
def register(payload: RegisterRequest):
    email = payload.email.strip().lower()
    password = payload.password.strip()
    full_name = payload.full_name.strip() if payload.full_name else None

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    # 1) Check if email already exists
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # 2) Create the user
    user_id = create_user(email=email, password=password, full_name=full_name)
    return {"status": "ok", "user_id": user_id}
