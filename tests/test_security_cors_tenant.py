"""P0 Automated Test Suite: CORS Security & Tenant Isolation Verification.

Tests:
1. Allowed development and production origins receive valid CORS response headers.
2. Arbitrary external origins (e.g. evil-attacker.com) are rejected.
3. Arbitrary Vercel subdomains (e.g. attacker.vercel.app) are rejected (no wildcard vulnerability).
4. Arbitrary Railway subdomains (e.g. attacker.railway.app) are rejected.
5. Preflight OPTIONS request validates allowed methods and headers.
6. FAISS path traversal attempt (e.g. ../../etc or ..\\secret) is safely blocked.
7. Project ID with invalid characters is rejected.
8. Cross-tenant agent memory isolation enforces physical separation.
"""

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
from main import app
from zoe.knowledge.retriever import search, search_async, _resolve_safe_index_path
from zoe.agents.memory import AgentMemoryManager


@pytest.fixture
def api_client():
    """Test client for FastAPI CORS and route security."""
    return TestClient(app)


def test_cors_allowed_development_origin(api_client):
    """Allowed origin (http://localhost:3000) must receive CORS headers."""
    headers = {
        "Origin": "http://localhost:3000",
    }
    response = api_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_allowed_railway_production_origin(api_client):
    """Explicitly configured production domain must receive CORS headers."""
    headers = {
        "Origin": "https://zoe-dashboard-production-74e063ad.up.railway.app",
    }
    response = api_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://zoe-dashboard-production-74e063ad.up.railway.app"


def test_cors_rejects_unknown_attacker_domain(api_client):
    """Unknown attacker domain must NOT receive access-control-allow-origin header."""
    headers = {
        "Origin": "https://evil-attacker.com",
    }
    response = api_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_rejects_arbitrary_vercel_subdomain(api_client):
    """Wildcard Vercel subdomains (e.g. evil-phishing.vercel.app) must be rejected."""
    headers = {
        "Origin": "https://evil-phishing.vercel.app",
    }
    response = api_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_rejects_arbitrary_railway_subdomain(api_client):
    """Wildcard Railway subdomains (e.g. evil-app.up.railway.app) must be rejected."""
    headers = {
        "Origin": "https://evil-app.up.railway.app",
    }
    response = api_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_options_allowed(api_client):
    """Preflight OPTIONS request for trusted origin returns allowed methods and headers."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    response = api_client.options("/api/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    allowed_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed_methods
    assert "OPTIONS" in allowed_methods


def test_tenant_faiss_path_traversal_blocked(tmp_path: Path):
    """Path traversal in FAISS index lookup must be safely blocked and return None."""
    base_dir = tmp_path / "indexes"
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1. Traversal using ../
    path_traversal = _resolve_safe_index_path(base_dir, "../../other_project")
    assert path_traversal is None

    # 2. Windows-style traversal
    path_win_traversal = _resolve_safe_index_path(base_dir, "..\\other_project")
    assert path_win_traversal is None

    # 3. Path with invalid special characters
    path_special = _resolve_safe_index_path(base_dir, "proj;rm -rf /")
    assert path_special is None

    # 4. Legitimate project ID resolves correctly
    legit_path = _resolve_safe_index_path(base_dir, "project_alpha-123")
    assert legit_path is not None
    assert legit_path == (base_dir / "project_alpha-123" / "index.faiss").resolve()

    # 5. Search with traversal project_id returns empty list safely
    results = search("../../secret_project", "test query", index_dir=base_dir)
    assert results == []


def test_cross_tenant_memory_isolation():
    """Agent memory must strictly partition records between tenants."""
    mem = AgentMemoryManager()

    # Org A saves context
    mem.save_task_summary(
        agent_id="research_agent",
        session_id="task_001",
        summary="Project A has 10M total supply and private valuation $50M.",
        organization_id="org_alpha",
    )

    # Org B saves context
    mem.save_task_summary(
        agent_id="research_agent",
        session_id="task_002",
        summary="Project B has 100M total supply.",
        organization_id="org_beta",
    )

    # Query Org A
    ctx_a = mem.get_organization_memory("org_alpha", limit=10)
    assert len(ctx_a) == 1
    assert "Project A" in ctx_a[0]["summary"]
    assert "Project B" not in ctx_a[0]["summary"]

    # Query Org B
    ctx_b = mem.get_organization_memory("org_beta", limit=10)
    assert len(ctx_b) == 1
    assert "Project B" in ctx_b[0]["summary"]
    assert "Project A" not in ctx_b[0]["summary"]
