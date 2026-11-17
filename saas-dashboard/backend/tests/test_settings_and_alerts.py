"""Tests for Mega-Module 12: User Settings, Billing History, and Notification Center."""

import pytest
from fastapi.testclient import TestClient

from main import app, get_current_user


client = TestClient(app)


def test_billing_history_unauthenticated_returns_401():
    """Verify /api/billing/history requires authentication."""
    app.dependency_overrides.clear()
    res = client.get("/api/billing/history")
    assert res.status_code == 401


def test_alerts_unauthenticated_returns_401():
    """Verify /api/alerts requires authentication."""
    app.dependency_overrides.clear()
    res = client.get("/api/alerts")
    assert res.status_code == 401


def test_alerts_read_unauthenticated_returns_401():
    """Verify /api/alerts/read requires authentication."""
    app.dependency_overrides.clear()
    res = client.post("/api/alerts/read")
    assert res.status_code == 401


def test_get_alerts_and_mark_as_read_flow():
    """Verify user can fetch alerts and mark them as read."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-user-settings-1", "email": "user1@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # 1. Fetch alerts
        res = client.get("/api/alerts")
        assert res.status_code == 200
        alerts = res.json()
        assert isinstance(alerts, list)
        assert len(alerts) > 0

        # 2. Mark alerts as read
        read_res = client.post("/api/alerts/read")
        assert read_res.status_code == 200
        assert read_res.json().get("success") is True

        # 3. Refetch alerts and verify is_read is True
        res_after = client.get("/api/alerts")
        assert res_after.status_code == 200
        alerts_after = res_after.json()
        for a in alerts_after:
            assert a.get("is_read") is True
    finally:
        app.dependency_overrides.clear()


def test_billing_history_returns_list():
    """Verify /api/billing/history returns past invoices list."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-user-settings-1", "email": "user1@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        res = client.get("/api/billing/history")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


def test_update_user_profile():
    """Verify /api/user/profile updates display name."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-user-settings-1", "email": "user1@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        res = client.post("/api/user/profile", json={"display_name": "Captain Robbie"})
        assert res.status_code == 200
        body = res.json()
        assert body.get("success") is True
        assert body.get("display_name") == "Captain Robbie"
    finally:
        app.dependency_overrides.clear()


def test_update_user_password():
    """Verify /api/user/password updates password with validation."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-user-settings-1", "email": "user1@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # Invalid short password
        short_res = client.post("/api/user/password", json={"password": "123"})
        assert short_res.status_code == 400

        # Valid password
        res = client.post("/api/user/password", json={"password": "SecurePassword123!"})
        assert res.status_code == 200
        assert res.json().get("success") is True
    finally:
        app.dependency_overrides.clear()
