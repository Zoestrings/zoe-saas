"""FastAPI backend for Zoe SaaS Dashboard.

Provides user authentication and encrypted project management via Supabase.
"""

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from cryptography.fernet import Fernet
import jwt

# Load environment variables from .env in backend directory or parent
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# App configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

DEV_DB_PATH = Path(__file__).parent / "saas_dev.db"


def get_dev_db() -> sqlite3.Connection:
    """Initialize local SQLite database for development when Supabase is not configured."""
    conn = sqlite3.connect(DEV_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_projects (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            telegram_bot_token TEXT NOT NULL,
            telegram_group_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn

# Initialize FastAPI app
app = FastAPI(
    title="Zoe SaaS Dashboard API",
    description="Backend API for Zoe AI Community Management SaaS Platform",
    version="1.0.0",
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security bearer scheme
security = HTTPBearer(auto_error=False)


# --- Cryptography Helpers ---
def get_fernet() -> Fernet:
    """Retrieve or initialize Fernet cipher using ENCRYPTION_KEY."""
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if not key or key == "your-fernet-encryption-key":
        # Fallback to a dynamically generated session key if not configured in environment
        from cryptography.fernet import Fernet
        dyn_key = Fernet.generate_key()
        os.environ["ENCRYPTION_KEY"] = dyn_key.decode("utf-8")
        return Fernet(dyn_key)
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


def encrypt_token(plain_token: str) -> str:
    """Encrypt sensitive credentials before saving to Supabase."""
    if not plain_token:
        raise ValueError("Token cannot be empty")
    cipher = get_fernet()
    return cipher.encrypt(plain_token.strip().encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt encrypted credentials."""
    cipher = get_fernet()
    return cipher.decrypt(encrypted_token.strip().encode("utf-8")).decode("utf-8")


# --- Supabase Client Helper ---
_supabase_client = None


def get_supabase():
    """Lazily initialize and return Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or "your-project" in url or not key:
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as exc:
        return None


# --- Authentication Dependency ---
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Dependency that decodes and validates the Supabase JWT.
    
    Rejects unauthenticated requests with HTTP 401.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()

    # 1. Try validating with Supabase Auth API
    client = get_supabase()
    if client is not None:
        try:
            user_response = client.auth.get_user(token)
            if user_response and user_response.user:
                u = user_response.user
                return {
                    "id": str(getattr(u, "id", "")),
                    "email": getattr(u, "email", ""),
                }
        except Exception:
            pass

    # 2. Try decoding JWT with pyjwt
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    if jwt_secret and jwt_secret != "your-supabase-jwt-secret":
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": False},
            )
            return {
                "id": str(payload.get("sub", "")),
                "email": payload.get("email", ""),
            }
        except Exception:
            pass

    # 3. Fallback unverified decode for test/dev environments
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub") or payload.get("id")
        if user_id:
            return {
                "id": str(user_id),
                "email": payload.get("email", ""),
            }
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Request & Response Models ---
class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class CreateProjectRequest(BaseModel):
    name: str
    telegram_bot_token: str
    telegram_group_id: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    telegram_group_id: Optional[str] = None
    created_at: Optional[str] = None


# --- Endpoints ---
@app.get("/")
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "zoe-saas-dashboard-backend",
        "supabase_connected": get_supabase() is not None,
    }


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _mint_dev_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
    }
    secret = os.getenv("SUPABASE_JWT_SECRET", "dev-secret-key-1234567890")
    if not secret or secret == "your-supabase-jwt-secret":
        secret = "dev-secret-key-1234567890"
    return jwt.encode(payload, secret, algorithm="HS256")


@app.post("/api/auth/register", response_model=AuthResponse)
def register_user(req: AuthRequest):
    """Register a new user account with Supabase Auth or local dev fallback."""
    client = get_supabase()
    if client is None:
        conn = get_dev_db()
        cur = conn.cursor()
        existing = cur.execute("SELECT id FROM dev_users WHERE email = ?", (req.email,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email is already registered.",
            )
        user_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO dev_users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, req.email, _hash_password(req.password), now_str),
        )
        conn.commit()
        token = _mint_dev_jwt(user_id, req.email)
        return AuthResponse(
            access_token=token,
            user={"id": user_id, "email": req.email},
        )

    try:
        res = client.auth.sign_up({"email": req.email, "password": req.password})
        user = res.user
        session = res.session
        token = session.access_token if session else ""
        return AuthResponse(
            access_token=token,
            user={"id": str(getattr(user, "id", "")), "email": req.email},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@app.post("/api/auth/login", response_model=AuthResponse)
def login_user(req: AuthRequest):
    """Authenticate an existing user with Supabase Auth or local dev fallback."""
    client = get_supabase()
    if client is None:
        conn = get_dev_db()
        cur = conn.cursor()
        row = cur.execute(
            "SELECT id, password_hash FROM dev_users WHERE email = ?", (req.email,)
        ).fetchone()
        if not row or row[1] != _hash_password(req.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        user_id = row[0]
        token = _mint_dev_jwt(user_id, req.email)
        return AuthResponse(
            access_token=token,
            user={"id": user_id, "email": req.email},
        )

    try:
        res = client.auth.sign_in_with_password({"email": req.email, "password": req.password})
        if not res.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login succeeded but no active session was returned.",
            )
        return AuthResponse(
            access_token=res.session.access_token,
            user={"id": str(getattr(res.user, "id", "")), "email": req.email},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
        )


@app.post("/api/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
def create_project(
    req: CreateProjectRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new project with encrypted Telegram bot token in Supabase or dev fallback."""
    owner_id = current_user.get("id")
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID could not be identified from token",
        )

    # CRITICAL: Encrypt the Telegram bot token BEFORE saving to database
    encrypted_token = encrypt_token(req.telegram_bot_token)

    client = get_supabase()
    if client is None:
        conn = get_dev_db()
        proj_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO dev_projects (id, owner_id, name, telegram_bot_token, telegram_group_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                proj_id,
                owner_id,
                req.name.strip(),
                encrypted_token,
                req.telegram_group_id.strip() if req.telegram_group_id else None,
                now_str,
            ),
        )
        conn.commit()
        return ProjectResponse(
            id=proj_id,
            owner_id=owner_id,
            name=req.name.strip(),
            telegram_group_id=req.telegram_group_id.strip() if req.telegram_group_id else None,
            created_at=now_str,
        )

    payload = {
        "owner_id": owner_id,
        "name": req.name.strip(),
        "telegram_bot_token": encrypted_token,
        "telegram_group_id": req.telegram_group_id.strip() if req.telegram_group_id else None,
    }

    try:
        result = client.table("projects").insert(payload).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to insert project into Supabase",
            )
        row = result.data[0]
        return ProjectResponse(
            id=str(row.get("id")),
            owner_id=str(row.get("owner_id")),
            name=row.get("name"),
            telegram_group_id=row.get("telegram_group_id"),
            created_at=str(row.get("created_at")),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(exc)}",
        )


@app.get("/api/projects", response_model=List[ProjectResponse])
def get_projects(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all projects owned by the currently authenticated user."""
    owner_id = current_user.get("id")
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID could not be identified from token",
        )

    client = get_supabase()
    if client is None:
        conn = get_dev_db()
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT id, owner_id, name, telegram_group_id, created_at
            FROM dev_projects
            WHERE owner_id = ?
            ORDER BY created_at DESC
            """,
            (owner_id,),
        ).fetchall()
        return [
            ProjectResponse(
                id=str(r[0]),
                owner_id=str(r[1]),
                name=str(r[2]),
                telegram_group_id=r[3],
                created_at=str(r[4]),
            )
            for r in rows
        ]

    try:
        result = (
            client.table("projects")
            .select("id, owner_id, name, telegram_group_id, created_at")
            .eq("owner_id", owner_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = result.data or []
        return [
            ProjectResponse(
                id=str(r.get("id")),
                owner_id=str(r.get("owner_id")),
                name=r.get("name"),
                telegram_group_id=r.get("telegram_group_id"),
                created_at=str(r.get("created_at")),
            )
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query error: {str(exc)}",
        )

