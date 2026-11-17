"""Tests for Super Admin Master Control endpoints (Mega-Module 10)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app, get_current_user


client = TestClient(app)


def test_admin_overview_requires_super_admin():
    """Verify non-super-admins receive 403 Forbidden on /api/admin/overview."""
    app.dependency_overrides.clear()
    regular_user = {"id": "user-regular-123", "email": "user@example.com", "role": "project_owner"}
    app.dependency_overrides[get_current_user] = lambda: regular_user

    try:
        response = client.get("/api/admin/overview")
        assert response.status_code == 403
        assert "Super Admin" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_projects_requires_super_admin():
    """Verify non-super-admins receive 403 Forbidden on /api/admin/projects."""
    app.dependency_overrides.clear()
    regular_user = {"id": "user-regular-123", "email": "user@example.com", "role": "authenticated"}
    app.dependency_overrides[get_current_user] = lambda: regular_user

    try:
        response = client.get("/api/admin/projects")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_overview_success():
    """Verify super-admin can access /api/admin/overview successfully."""
    app.dependency_overrides.clear()
    admin_user = {"id": "superadmin-001", "email": "admin@zoe.network", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: admin_user

    try:
        response = client.get("/api/admin/overview")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_revenue" in data["summary"]
        assert "total_users" in data["summary"]
        assert "active_bots" in data["summary"]
        assert "recent_signups" in data
        assert "revenue_chart" in data
        assert isinstance(data["revenue_chart"], list)
    finally:
        app.dependency_overrides.clear()


def test_admin_projects_master_list():
    """Verify super-admin can fetch master projects table."""
    app.dependency_overrides.clear()
    admin_user = {"id": "superadmin-001", "email": "admin@zoe.network", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: admin_user

    try:
        response = client.get("/api/admin/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            proj = data[0]
            assert "id" in proj
            assert "name" in proj
            assert "owner_email" in proj
            assert "status" in proj
            assert "plan" in proj
    finally:
        app.dependency_overrides.clear()


def test_admin_suspend_and_activate_project():
    """Verify super-admin can suspend and reactivate a project."""
    app.dependency_overrides.clear()
    admin_user = {"id": "superadmin-001", "email": "admin@zoe.network", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: admin_user

    test_proj_id = "onelove"

    try:
        with patch("main.call_engine", return_value={"status": "ok"}):
            # 1. Suspend
            res_suspend = client.post(f"/api/admin/projects/{test_proj_id}/suspend")
            assert res_suspend.status_code == 200
            assert res_suspend.json()["status"] == "suspended"

            # 2. Reactivate
            res_activate = client.post(f"/api/admin/projects/{test_proj_id}/activate")
            assert res_activate.status_code == 200
            assert res_activate.json()["status"] == "live"
    finally:
        app.dependency_overrides.clear()


def test_admin_health_endpoint():
    """Verify super-admin can inspect system health."""
    app.dependency_overrides.clear()
    admin_user = {"id": "superadmin-001", "email": "admin@zoe.network", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: admin_user

    try:
        response = client.get("/api/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert "Online" in data["fastapi"]
        assert "database" in data
        assert "solana_rpc" in data
        assert "engine" in data
    finally:
        app.dependency_overrides.clear()
