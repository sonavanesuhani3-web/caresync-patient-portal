# auth_api.py
# CareSync Day 7 - Authentication and Authorisation Backend
#
# This file handles register, login, logout, token refresh, and dashboards.
#
# Run this file with:
#   uvicorn auth_api:app --reload --port 8002
#
# Open: http://127.0.0.1:8002/docs to test all endpoints.

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
import mysql.connector
import bcrypt
import re

# Create the FastAPI application
app = FastAPI(title="CareSync Auth API")

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Token Settings ────────────────────────────────────────────────────────────
SECRET_KEY            = "caresync-day7-secret-key-change-in-production"
ALGORITHM             = "HS256"
ACCESS_EXPIRE_MINUTES = 15  # Access token expires in 15 minutes
REFRESH_EXPIRE_DAYS   = 7   # Refresh token expires in 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ── Database Connection ───────────────────────────────────────────────────────
def get_db():
    conn = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="caresync"
    )
    cur = conn.cursor(dictionary=True)
    return conn, cur


# ── Password Helpers ──────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()

def verify_password(plain: str, hashed: str) -> bool:
    # Handles both plain-text matches (if seed stores plain passwords) and bcrypt hashes
    if plain == hashed:
        return True
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── Token Helpers ─────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["sub"]  = str(data["sub"])
    payload["exp"]  = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    payload["type"] = "access"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["sub"]  = str(data["sub"])
    payload["exp"]  = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload["type"] = "refresh"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def store_refresh_token(user_id: int, token: str):
    conn, cur = get_db()
    expires = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    cur.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
        (int(user_id), token, expires)
    )
    conn.commit()
    cur.close()
    conn.close()


# ── Password Strength Check ───────────────────────────────────────────────────
def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@#$%^&+=!]", password):
        return False
    return True


# ── Request Models ────────────────────────────────────────────────────────────
# Plain 'str' is used for email to support internal domain formats like .local
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str       # "doctor" or "patient"
    linked_id: int  # doctor_id or patient_id from the existing table

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str


# ── Reusable Dependency: get_current_user ─────────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload    = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id    = int(payload.get("sub"))
        token_type = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_error

    except (JWTError, TypeError, ValueError):
        raise credentials_error

    conn, cur = get_db()
    cur.execute(
        "SELECT user_id, email, role, linked_id FROM users WHERE user_id = %s AND is_active = 1",
        (user_id,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise credentials_error

    return user


# ── ENDPOINT: POST /register ──────────────────────────────────────────────────
@app.post("/register", status_code=201)
def register(req: RegisterRequest):
    if not is_strong_password(req.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters and include an uppercase letter, a number, and a special character (@#$%^&+=!)."
        )

    conn, cur = get_db()

    cur.execute("SELECT user_id FROM users WHERE email = %s", (req.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=409, detail="Email already registered.")

    hashed = hash_password(req.password)
    cur.execute(
        "INSERT INTO users (email, password_hash, role, linked_id) VALUES (%s, %s, %s, %s)",
        (req.email, hashed, req.role, req.linked_id)
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()

    return {"message": "Account created.", "user_id": new_id}


# ── ENDPOINT: POST /login ─────────────────────────────────────────────────────
@app.post("/login")
def login(req: LoginRequest):
    conn, cur = get_db()
    cur.execute(
        "SELECT user_id, email, password_hash, role, linked_id FROM users WHERE email = %s AND is_active = 1",
        (req.email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    INVALID_MSG = "Invalid email or password."

    if not user:
        raise HTTPException(status_code=401, detail=INVALID_MSG)

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail=INVALID_MSG)

    token_data    = {"sub": user["user_id"], "role": user["role"]}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    store_refresh_token(user["user_id"], refresh_token)

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "role":          user["role"],
        "linked_id":     user["linked_id"]
    }


# ── ENDPOINT: POST /refresh ───────────────────────────────────────────────────
@app.post("/refresh")
def refresh_token_endpoint(req: RefreshRequest):
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired refresh token."
    )

    try:
        payload    = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id    = int(payload.get("sub"))
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise credentials_error
    except (JWTError, TypeError, ValueError):
        raise credentials_error

    conn, cur = get_db()
    cur.execute(
        "SELECT token_id FROM refresh_tokens WHERE token_hash = %s AND user_id = %s",
        (req.refresh_token, user_id)
    )
    record = cur.fetchone()

    if not record:
        cur.close()
        conn.close()
        raise credentials_error

    cur.execute(
        "DELETE FROM refresh_tokens WHERE token_hash = %s",
        (req.refresh_token,)
    )
    conn.commit()
    cur.close()
    conn.close()

    token_data   = {"sub": user_id, "role": payload.get("role")}
    access_token = create_access_token(token_data)
    new_refresh  = create_refresh_token(token_data)
    store_refresh_token(user_id, new_refresh)

    return {
        "access_token":  access_token,
        "refresh_token": new_refresh,
        "token_type":    "bearer"
    }


# ── ENDPOINT: POST /logout ────────────────────────────────────────────────────
@app.post("/logout")
def logout(req: RefreshRequest):
    conn, cur = get_db()
    cur.execute(
        "DELETE FROM refresh_tokens WHERE token_hash = %s",
        (req.refresh_token,)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Logged out."}


# ── ENDPOINT: GET /me ─────────────────────────────────────────────────────────
@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id":   current_user["user_id"],
        "email":     current_user["email"],
        "role":      current_user["role"],
        "linked_id": current_user["linked_id"]
    }


# ── ENDPOINT: GET /dashboard/doctor ──────────────────────────────────────────
@app.get("/dashboard/doctor")
def doctor_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Access denied. Doctors only.")

    doctor_id = current_user["linked_id"]
    conn, cur = get_db()

    cur.execute("""
        SELECT
            a.appointment_id,
            p.full_name        AS patient_name,
            p.blood_group,
            p.phone            AS phone_number,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.reason
        FROM appointment a
        JOIN patient p ON p.patient_id = a.patient_id
        WHERE a.doctor_id = %s
        ORDER BY a.appointment_date DESC
        LIMIT 10
    """, (doctor_id,))

    appointments = cur.fetchall()

    for appt in appointments:
        if appt["appointment_date"]:
            appt["appointment_date"] = str(appt["appointment_date"])
        if appt["appointment_time"]:
            appt["appointment_time"] = str(appt["appointment_time"])

    cur.close()
    conn.close()

    return {
        "doctor_id":          doctor_id,
        "today_appointments": appointments
    }


# ── ENDPOINT: GET /dashboard/patient ─────────────────────────────────────────
@app.get("/dashboard/patient")
def patient_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Access denied. Patients only.")

    patient_id = current_user["linked_id"]
    conn, cur  = get_db()

    cur.execute("""
        SELECT
            a.appointment_id,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.reason,
            d.full_name      AS doctor_name,
            d.specialisation,
            d.department
        FROM appointment a
        JOIN doctor d ON d.doctor_id = a.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC
        LIMIT 10
    """, (patient_id,))

    appointments = cur.fetchall()

    for appt in appointments:
        if appt["appointment_date"]:
            appt["appointment_date"] = str(appt["appointment_date"])
        if appt["appointment_time"]:
            appt["appointment_time"] = str(appt["appointment_time"])

    cur.execute("""
        SELECT
            b.bill_id,
            b.bill_date,
            b.total_amount,
            b.amount_paid,
            b.discount,
            b.status
        FROM billing b
        WHERE b.patient_id = %s
        ORDER BY b.bill_date DESC
        LIMIT 10
    """, (patient_id,))

    bills = cur.fetchall()

    for bill in bills:
        bill["bill_date"] = str(bill["bill_date"])

    cur.close()
    conn.close()

    return {
        "patient_id":   patient_id,
        "appointments": appointments,
        "bills":        bills
    }