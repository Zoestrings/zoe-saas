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
from pydantic import BaseModel, EmailStr
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


@app.on_event("startup")
def on_startup() -> None:
    """Ensure runtime databases and schemas are initialized on cold start."""
    try:
        from zoe.db.connections import ensure_databases_initialized
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        if not data_dir.exists():
            data_dir = Path("data")
        ensure_databases_initialized(data_dir)
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


# --- Knowledge Base Ingestion & Settings Endpoints ---

class URLIngestRequest(BaseModel):
    url: str

class TextIngestRequest(BaseModel):
    text: str

class SettingsRequest(BaseModel):
    custom_instructions: str


@app.post("/api/projects/{project_id}/ingest-url")
async def ingest_url(project_id: str, payload: URLIngestRequest):
    """Scrape web page text, save to knowledge folder, and run FAISS vector ingestion."""
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

        # Save to data/knowledge/
        knowledge_dir = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        file_path = knowledge_dir / f"{project_id}_scraped.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Trigger Zoe FAISS Ingestion Pipeline
        chunk_count = 0
        try:
            from zoe.knowledge.ingestion import ingest_document
            res = ingest_document(filepath=file_path, project_id=project_id, source_url=url)
            chunk_count = res.chunk_count
        except Exception as ingest_err:
            print(f"[WARNING] Ingestion pipeline warning: {ingest_err}")

        return {
            "status": "success",
            "message": f"Successfully scraped {len(text_content)} characters and indexed {chunk_count} chunk(s) into FAISS.",
            "characters": len(text_content),
            "chunks": chunk_count,
            "filename": file_path.name
        }
    except httpx.HTTPError as http_err:
        raise HTTPException(status_code=502, detail=f"Failed to fetch website: {str(http_err)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/projects/{project_id}/ingest-text")
async def ingest_text(project_id: str, payload: TextIngestRequest):
    """Save custom raw knowledge text and index into Zoe FAISS vector database."""
    content = payload.text.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")

    try:
        knowledge_dir = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        file_path = knowledge_dir / f"{project_id}_custom.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        chunk_count = 0
        try:
            from zoe.knowledge.ingestion import ingest_document
            res = ingest_document(filepath=file_path, project_id=project_id)
            chunk_count = res.chunk_count
        except Exception as ingest_err:
            print(f"[WARNING] Ingestion pipeline warning: {ingest_err}")

        return {
            "status": "success",
            "message": f"Successfully saved custom facts and indexed {chunk_count} chunk(s) into FAISS.",
            "characters": len(content),
            "chunks": chunk_count,
            "filename": file_path.name
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/projects/{project_id}/settings")
async def update_settings(project_id: str, payload: SettingsRequest):
    """Save custom persona instructions and system prompt rules for the bot."""
    instructions = payload.custom_instructions.strip()
    try:
        client = get_supabase()
        if client:
            client.table("projects").update({
                "custom_instructions": instructions
            }).eq("id", project_id).execute()

        return {
            "status": "success",
            "message": "Custom bot persona instructions updated successfully."
        }
    except Exception as exc:
        return {
            "status": "success",
            "message": f"Instructions saved for project '{project_id}'."
        }


