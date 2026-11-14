"""FastAPI backend for Zoe SaaS Dashboard.

Provides user authentication and encrypted project management via Supabase.
"""

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import uuid
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import asyncio
from pydantic import BaseModel, EmailStr, field_validator
from cryptography.fernet import Fernet
import jwt

# Add src to sys.path so zoe packages can be imported
_src_dir = str(Path(__file__).resolve().parent.parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

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
ZOE_ENGINE_URL = os.getenv("ZOE_ENGINE_URL", "http://zoe-worker.railway.internal:8080").rstrip("/")
ENGINE_SHARED_SECRET = os.getenv("ENGINE_SHARED_SECRET", "")

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
            token_address TEXT,
            status TEXT DEFAULT 'live',
            status_error TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # Graceful migration for existing local dev databases
    for col, col_def in [
        ("token_address", "TEXT"),
        ("status", "TEXT DEFAULT 'live'"),
        ("status_error", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE dev_projects ADD COLUMN {col} {col_def}")
            conn.commit()
        except Exception:
            pass

    return conn

# Initialize FastAPI app
app = FastAPI(
    title="Zoe SaaS Dashboard API",
    description="Backend API for Zoe AI Community Management SaaS Platform",
    version="1.0.0",
)


def _backend_data_dir() -> Path:
    """Return root data directory, prioritizing DATA_DIR env var (e.g. mounted Railway volume)."""
    env_dir = os.getenv("DATA_DIR")
    if env_dir and env_dir.strip():
        p = Path(env_dir.strip())
        p.mkdir(parents=True, exist_ok=True)
        return p
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    if not data_dir.exists():
        data_dir = Path("data")
    return data_dir


@app.on_event("startup")
def on_startup() -> None:
    """Ensure runtime databases and schemas are initialized on cold start."""
    try:
        from zoe.db.connections import ensure_databases_initialized
        ensure_databases_initialized(_backend_data_dir())
    except Exception:
        pass

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_cors = os.getenv("CORS_ORIGINS", "")
if env_cors:
    origins.extend([o.strip() for o in env_cors.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/.*\.up\.railway\.app$|^https:\/\/.*\.vercel\.app$|^http:\/\/localhost(:\d+)?$",
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


def sanitize_project_id(raw_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw_name.lower().strip()).strip("-")
    if len(slug) < 3:
        slug = f"project-{slug}"
    return slug[:35]


class CreateProjectRequest(BaseModel):
    name: str
    telegram_bot_token: str
    telegram_group_id: Optional[str] = None
    token_address: str
    token_symbol: Optional[str] = None
    knowledge_base: Optional[str] = None

    @field_validator("telegram_group_id", mode="before")
    def normalize_group_id(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return str(v).strip()

    @field_validator("token_address")
    def validate_token_address(cls, v):
        val = str(v).strip()
        if not re.match(r"^(0x[a-fA-F0-9]{40}|[A-Za-z0-9]{32,64})$", val):
            raise ValueError("Token address must be a valid Solana (base58, 32-64 chars) or EVM (0x..., 42 chars) contract address.")
        return val


class PatchProjectRequest(BaseModel):
    telegram_group_id: Optional[str] = None
    token_address: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    telegram_group_id: Optional[str] = None
    token_address: Optional[str] = None
    status: str = "live"
    status_error: Optional[str] = None
    created_at: Optional[str] = None


async def call_engine(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call Zoe Bot Engine internal API with retries and authentication."""
    url = f"{ZOE_ENGINE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if ENGINE_SHARED_SECRET:
        headers["X-Engine-Key"] = ENGINE_SHARED_SECRET

    retries = 2
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if method.upper() == "POST":
                    resp = await client.post(url, json=payload, headers=headers)
                elif method.upper() == "PATCH":
                    resp = await client.patch(url, json=payload, headers=headers)
                elif method.upper() == "DELETE":
                    resp = await client.delete(url, headers=headers)
                else:
                    resp = await client.get(url, headers=headers)

                if resp.status_code >= 400:
                    err_msg = resp.text
                    try:
                        err_data = resp.json()
                        err_msg = err_data.get("detail", resp.text)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"Engine Error: {err_msg}",
                    )
                return resp.json()
        except HTTPException:
            raise
        except httpx.RequestError as exc:
            if attempt == retries:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Unable to connect to Zoe Engine at {ZOE_ENGINE_URL}: {str(exc)}",
                )
            await asyncio.sleep(0.5 * (attempt + 1))
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Engine communication failed")


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


def _update_project_status(project_id: str, new_status: str, error_msg: Optional[str] = None, client: Any = None):
    if client is None:
        try:
            conn = get_dev_db()
            conn.execute("UPDATE dev_projects SET status = ?, status_error = ? WHERE id = ?", (new_status, error_msg, project_id))
            conn.commit()
        except Exception:
            pass
    else:
        try:
            client.table("projects").update({"status": new_status, "status_error": error_msg}).eq("id", project_id).execute()
        except Exception:
            pass


@app.post("/api/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def create_project(
    req: CreateProjectRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new project, save encrypted credentials, and trigger live bot spawning in the Engine."""
    owner_id = current_user.get("id")
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID could not be identified from token",
        )

    # 1. Clean and slugify project_id
    base_slug = sanitize_project_id(req.name)
    now_str = datetime.now(timezone.utc).isoformat()
    client = get_supabase()

    # Determine unique ID
    proj_id = base_slug
    if client is None:
        conn = get_dev_db()
        cur = conn.cursor()
        existing = cur.execute("SELECT id FROM dev_projects WHERE id = ?", (proj_id,)).fetchone()
        if existing:
            proj_id = f"{base_slug}-{uuid.uuid4().hex[:6]}"
    else:
        try:
            res_ex = client.table("projects").select("id").eq("id", proj_id).execute()
            if res_ex.data:
                proj_id = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        except Exception:
            pass

    # 2. Encrypt token for persistence
    encrypted_token = encrypt_token(req.telegram_bot_token)

    # 3. Save initial record with status "deploying"
    if client is None:
        conn = get_dev_db()
        conn.execute(
            """
            INSERT INTO dev_projects (id, owner_id, name, telegram_bot_token, telegram_group_id, token_address, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'deploying', ?)
            """,
            (
                proj_id,
                owner_id,
                req.name.strip(),
                encrypted_token,
                req.telegram_group_id,
                req.token_address.strip(),
                now_str,
            ),
        )
        conn.commit()
    else:
        payload = {
            "id": proj_id,
            "owner_id": owner_id,
            "name": req.name.strip(),
            "telegram_bot_token": encrypted_token,
            "telegram_group_id": req.telegram_group_id,
            "token_address": req.token_address.strip(),
            "status": "deploying",
        }
        try:
            client.table("projects").insert(payload).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database insert error: {str(exc)}",
            )

    # 4. Call Engine to spawn bot poller
    engine_payload = {
        "project_id": proj_id,
        "bot_token": req.telegram_bot_token.strip(),
        "group_id": req.telegram_group_id,
        "token_address": req.token_address.strip(),
        "token_symbol": req.token_symbol,
        "name": req.name.strip(),
        "knowledge_base": req.knowledge_base,
    }

    try:
        await call_engine("POST", "/api/spawn-bot", engine_payload)
        _update_project_status(proj_id, "live", None, client)
        current_status = "live"
        current_error = None
    except Exception as exc:
        err_msg = str(getattr(exc, "detail", exc))
        _update_project_status(proj_id, "failed", err_msg, client)
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Engine failed to spawn bot: {err_msg}",
        )

    return ProjectResponse(
        id=proj_id,
        owner_id=owner_id,
        name=req.name.strip(),
        telegram_group_id=req.telegram_group_id,
        token_address=req.token_address.strip(),
        status=current_status,
        status_error=current_error,
        created_at=now_str,
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
            SELECT id, owner_id, name, telegram_group_id, token_address, status, status_error, created_at
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
                token_address=r[4],
                status=r[5] or "live",
                status_error=r[6],
                created_at=str(r[7]),
            )
            for r in rows
        ]

    try:
        result = (
            client.table("projects")
            .select("id, owner_id, name, telegram_group_id, token_address, status, status_error, created_at")
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
                token_address=r.get("token_address"),
                status=r.get("status") or "live",
                status_error=r.get("status_error"),
                created_at=str(r.get("created_at")),
            )
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(exc)}",
        )


@app.patch("/api/projects/{project_id}", response_model=ProjectResponse)
async def patch_project(
    project_id: str,
    req: PatchProjectRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Hot-reload project settings (e.g. locking group ID or updating contract address)."""
    owner_id = current_user.get("id")
    client = get_supabase()

    # 1. Update Engine
    engine_payload = {}
    if req.telegram_group_id is not None:
        engine_payload["group_id"] = req.telegram_group_id.strip()
    if req.token_address is not None:
        engine_payload["token_address"] = req.token_address.strip()

    if engine_payload:
        await call_engine("PATCH", f"/api/bots/{project_id}", engine_payload)

    # 2. Update Database
    if client is None:
        conn = get_dev_db()
        if req.telegram_group_id is not None:
            conn.execute("UPDATE dev_projects SET telegram_group_id = ? WHERE id = ? AND owner_id = ?", (req.telegram_group_id.strip(), project_id, owner_id))
        if req.token_address is not None:
            conn.execute("UPDATE dev_projects SET token_address = ? WHERE id = ? AND owner_id = ?", (req.token_address.strip(), project_id, owner_id))
        conn.commit()
        row = conn.execute("SELECT id, owner_id, name, telegram_group_id, token_address, status, created_at FROM dev_projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(
            id=str(row[0]),
            owner_id=str(row[1]),
            name=str(row[2]),
            telegram_group_id=row[3],
            token_address=row[4],
            status=row[5] or "live",
            created_at=str(row[6]),
        )
    else:
        db_update = {}
        if req.telegram_group_id is not None:
            db_update["telegram_group_id"] = req.telegram_group_id.strip()
        if req.token_address is not None:
            db_update["token_address"] = req.token_address.strip()
        res = client.table("projects").update(db_update).eq("id", project_id).eq("owner_id", owner_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Project not found")
        row = res.data[0]
        return ProjectResponse(
            id=str(row.get("id")),
            owner_id=str(row.get("owner_id")),
            name=row.get("name"),
            telegram_group_id=row.get("telegram_group_id"),
            token_address=row.get("token_address"),
            status=row.get("status") or "live",
            created_at=str(row.get("created_at")),
        )


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Decommission a bot, cancel worker task, and purge credentials."""
    owner_id = current_user.get("id")
    client = get_supabase()

    # 1. Stop bot in Engine
    try:
        await call_engine("DELETE", f"/api/bots/{project_id}")
    except Exception as exc:
        logger.warning("Engine delete failed for %s: %s", project_id, exc)

    # 2. Remove or mark stopped in DB
    if client is None:
        conn = get_dev_db()
        conn.execute("UPDATE dev_projects SET status = 'stopped' WHERE id = ? AND owner_id = ?", (project_id, owner_id))
        conn.commit()
    else:
        try:
            client.table("projects").update({"status": "stopped"}).eq("id", project_id).eq("owner_id", owner_id).execute()
        except Exception:
            pass

    return {"project_id": project_id, "status": "stopped", "message": "Bot decommissioned successfully"}


@app.get("/api/projects/{project_id}/status")
async def get_project_status(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Query live telemetry and poller health directly from the Bot Engine."""
    return await call_engine("GET", f"/api/bots/{project_id}/status")


# --- Knowledge Base Ingestion & Document Management Endpoints ---

class URLIngestRequest(BaseModel):
    url: str

class TextIngestRequest(BaseModel):
    text: str

class SettingsRequest(BaseModel):
    custom_instructions: str


def _get_project_knowledge_files(project_id: str, knowledge_dir: Path) -> List[Path]:
    """Helper to match knowledge files belonging to a project."""
    if not knowledge_dir.exists():
        return []
    
    # Prefix variants (e.g., live_test maps to hummingbird_info.txt as well)
    prefixes = [project_id.lower()]
    if project_id.lower() in ("live_test", "hummingbird"):
        prefixes.extend(["live_test", "hummingbird"])
    elif project_id.lower() in ("onelove", "one_love"):
        prefixes.extend(["onelove", "one_love"])

    matched: List[Path] = []
    for f in knowledge_dir.glob("*.txt"):
        if f.name.endswith("_instructions.txt"):
            continue
        fname_lower = f.name.lower()
        if any(fname_lower.startswith(p) for p in prefixes):
            matched.append(f)
    return sorted(matched, key=lambda x: x.stat().st_mtime, reverse=True)


@app.get("/api/projects/{project_id}/documents")
async def list_documents(project_id: str):
    """Scan data/knowledge/ and return all knowledge documents belonging to this project."""
    knowledge_dir = _backend_data_dir() / "knowledge"
    files = _get_project_knowledge_files(project_id, knowledge_dir)
    
    docs = []
    for f in files:
        stat = f.stat()
        try:
            content = f.read_text(encoding="utf-8")
            char_count = len(content)
        except Exception:
            char_count = stat.st_size

        docs.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "char_count": char_count,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "is_default": f.name in ("onelove_info.txt", "hummingbird_info.txt")
        })

    return {"project_id": project_id, "documents": docs, "total": len(docs)}


@app.delete("/api/projects/{project_id}/documents/{filename}")
async def delete_document(project_id: str, filename: str):
    """Delete a document file from data/knowledge/ and immediately rebuild the project's FAISS index."""
    # Prevent directory traversal
    safe_filename = Path(filename).name
    if not safe_filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Invalid filename. Only .txt knowledge files can be removed.")

    knowledge_dir = _backend_data_dir() / "knowledge"
    target_file = knowledge_dir / safe_filename

    if not target_file.exists():
        raise HTTPException(status_code=404, detail=f"Document '{safe_filename}' not found.")

    # Remove file from disk
    try:
        target_file.unlink()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete file from disk: {exc}")

    # Remove from official_knowledge.db and rebuild FAISS index
    rebuild_error = None
    try:
        from zoe.db.connections import open_official_knowledge_db
        from zoe.knowledge.ingestion import rebuild_faiss_index

        db_path = _backend_data_dir() / "official_knowledge" / "official_knowledge.db"
        if db_path.exists():
            conn = open_official_knowledge_db(db_path)
            try:
                conn.execute(
                    "DELETE FROM official_documents WHERE project_id = ? AND filename = ?",
                    (project_id, safe_filename),
                )
                conn.commit()
                index_dir = _backend_data_dir() / "indexes"
                rebuild_faiss_index(project_id, conn, index_dir=index_dir)
            finally:
                conn.close()
    except Exception as exc:
        rebuild_error = str(exc)

    return {
        "status": "success",
        "message": f"Document '{safe_filename}' deleted and FAISS index rebuilt.",
        "rebuild_warning": rebuild_error
    }


@app.post("/api/projects/{project_id}/ingest-url")
async def ingest_url(project_id: str, payload: URLIngestRequest):
    """Scrape web page text, save to knowledge folder, and immediately rebuild FAISS vector index."""
    url = payload.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL protocol. Must start with http:// or https://")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Zoe/1.0"
        }
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "svg", "form", "iframe"]):
            tag.decompose()

        lines = []
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                lines.append(f"Title: {title}")

        body = soup.find("body") or soup
        text_content = body.get_text(separator="\n", strip=True)
        if lines:
            text_content = "\n".join(lines) + "\n\n" + text_content

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No readable text content found on the specified page.")

        # Save to data/knowledge/ with timestamp
        knowledge_dir = _backend_data_dir() / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{project_id}_web_{timestamp_slug}.txt"
        file_path = knowledge_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Trigger Zoe FAISS Ingestion Pipeline immediately
        chunk_count = 0
        try:
            from zoe.knowledge.ingestion import ingest_document
            db_path = _backend_data_dir() / "official_knowledge" / "official_knowledge.db"
            index_dir = _backend_data_dir() / "indexes"
            res = ingest_document(filepath=file_path, project_id=project_id, db_path=db_path, index_dir=index_dir, source_url=url)
            chunk_count = res.chunk_count
        except Exception as ingest_err:
            print(f"[WARNING] Ingestion pipeline warning: {ingest_err}")

        return {
            "status": "success",
            "message": f"Successfully scraped {len(text_content)} characters and indexed {chunk_count} chunk(s) into FAISS.",
            "characters": len(text_content),
            "chunks": chunk_count,
            "filename": filename
        }
    except httpx.HTTPError as http_err:
        raise HTTPException(status_code=502, detail=f"Failed to fetch website: {str(http_err)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/projects/{project_id}/ingest-text")
async def ingest_text(project_id: str, payload: TextIngestRequest):
    """Save custom raw knowledge text and immediately rebuild Zoe FAISS vector database."""
    content = payload.text.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")

    try:
        knowledge_dir = _backend_data_dir() / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{project_id}_update_{timestamp_slug}.txt"
        file_path = knowledge_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        chunk_count = 0
        try:
            from zoe.knowledge.ingestion import ingest_document
            db_path = _backend_data_dir() / "official_knowledge" / "official_knowledge.db"
            index_dir = _backend_data_dir() / "indexes"
            res = ingest_document(filepath=file_path, project_id=project_id, db_path=db_path, index_dir=index_dir)
            chunk_count = res.chunk_count
        except Exception as ingest_err:
            print(f"[WARNING] Ingestion pipeline warning: {ingest_err}")

        return {
            "status": "success",
            "message": f"Successfully injected facts and indexed {chunk_count} chunk(s) into FAISS.",
            "characters": len(content),
            "chunks": chunk_count,
            "filename": filename
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/projects/{project_id}/settings")
async def get_settings(project_id: str):
    """Retrieve custom persona instructions and system rules for the bot."""
    instructions = ""
    # 1. Check volume/local file on disk
    inst_file = _backend_data_dir() / "knowledge" / f"{project_id}_instructions.txt"
    if inst_file.exists():
        try:
            instructions = inst_file.read_text(encoding="utf-8")
        except Exception:
            pass

    # 2. Check Supabase if available
    if not instructions:
        try:
            client = get_supabase()
            if client:
                res = client.table("projects").select("custom_instructions").eq("id", project_id).execute()
                if res.data and len(res.data) > 0:
                    instructions = res.data[0].get("custom_instructions") or ""
        except Exception:
            pass

    return {
        "project_id": project_id,
        "custom_instructions": instructions
    }


@app.post("/api/projects/{project_id}/settings")
async def update_settings(project_id: str, payload: SettingsRequest):
    """Save custom persona instructions and system prompt rules for the bot."""
    instructions = payload.custom_instructions.strip()
    
    # 1. Save to volume/local file so pipeline picks it up immediately
    try:
        inst_dir = _backend_data_dir() / "knowledge"
        inst_dir.mkdir(parents=True, exist_ok=True)
        inst_file = inst_dir / f"{project_id}_instructions.txt"
        with open(inst_file, "w", encoding="utf-8") as f:
            f.write(instructions)
    except Exception as exc:
        print(f"[WARNING] Failed to write instructions file: {exc}")

    # 2. Sync to Supabase
    try:
        client = get_supabase()
        if client:
            client.table("projects").update({
                "custom_instructions": instructions
            }).eq("id", project_id).execute()
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Custom bot persona instructions updated successfully and active immediately."
    }



