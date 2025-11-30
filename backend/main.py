# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.db import (
    get_users_count,
    create_user,
    get_user_by_email,
    verify_password,
    create_invite,
    get_invite_for_email,
    mark_invite_used,
)

from backend.notifications import send_email



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
    full_name: Optional[str] = None   # ✅ 3.9-safe

class LoginRequest(BaseModel):
    email: str
    password: str

class InviteCreateRequest(BaseModel):
    email: str
    invited_by_id: Optional[int] = None


@app.post("/invites/create")
def invites_create(payload: InviteCreateRequest):
    email = payload.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    invite_id = create_invite(email=email, invited_by_id=payload.invited_by_id)

    # Send "invite" email (console only for now)
    # inside create_invite() AFTER invite creation:

    subject = "Your Invitation to Circle — A Curated Community of Trusted Sellers"

    body = f"""
        Hello,

        A Circle member has extended a private invitation on your behalf.
        Membership is granted only when an existing member is willing to stand behind your character and your integrity.

        Circle is a curated environment for selling and discovering:
        vintage pieces, designer goods, artwork, craftwork, and unique personal items — always authentic, never counterfeit.

        Our community is built on three principles:

        Trust. Taste. Transparency.

        Every invitation represents a personal recommendation.
        Every member is responsible for the integrity of the people they invite.

        If you choose to join, you are affirming that you will uphold the same standards:
        authenticity, honesty, and respect in every transaction.

        Our guidelines:

        • List only authentic and original items
        • Conduct all transactions with honesty and professionalism
        • Invite only individuals you personally trust and would vouch for
        • Sellers contribute a 10% commission that supports Circle’s operations and curation

        Your invitation is now active.  
        Use this email address to join the Circle.

        Warmly,  
        Jo BoBa  
        Founder, Circle
        """
    send_email(email, subject, body)

    return {"status": "ok", "invite_id": invite_id}

@app.post("/auth/login")
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    user = get_user_by_email(email)
    if not user:
        # don't reveal which part is wrong
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    stored_hash = user["password_hash"]
    if not verify_password(password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "status": "ok",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
        },
    }


@app.get("/invites")
def invites_list():
    from backend.db import get_connection

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, invited_by_id, used_by_user_id, created_at, used_at
        FROM invites
        ORDER BY id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    return {
        "status": "ok",
        "invites": [dict(r) for r in rows],
    }



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

    # 5) send welcome email (console)
    subject = "Welcome to Circle"
    body = (
        f"Hi {full_name or email},\n\n"
        "Welcome to Circle! Your account has been created.\n"
        "You can now log in, create listings, and shop from curated closets.\n\n"
        "Love,\nCircle"
    )
    send_email(email, subject, body)

    return {"status": "ok", "user_id": user_id}


from backend.db import (
    get_users_count,
    create_user,
    get_user_by_email,
    verify_password,
)

@app.post("/auth/register")
def register(payload: RegisterRequest):
    email = payload.email.strip().lower()
    password = payload.password.strip()
    full_name = payload.full_name.strip() if payload.full_name else None

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    # 1) already registered?
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # 2) invite-only: require an unused invite for this email
    invite = get_invite_for_email(email)
    if not invite:
        raise HTTPException(
            status_code=403,
            detail="This email is not invited to Circle yet. Please ask a member to invite you.",
        )

    # 3) create user
    user_id = create_user(email=email, password=password, full_name=full_name)

    # 4) mark invite as used
    mark_invite_used(invite["id"], user_id)

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
