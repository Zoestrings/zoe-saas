"""Tests for Paper Trading Engine (Mega-Module 11)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app, get_current_user


client = TestClient(app)


def test_trading_wallet_unauthenticated_returns_401():
    """Verify /api/trading/wallet rejects unauthenticated callers with 401."""
    app.dependency_overrides.clear()
    res = client.get("/api/trading/wallet")
    assert res.status_code == 401


def test_trading_execute_unauthenticated_returns_401():
    """Verify /api/trading/execute rejects unauthenticated callers with 401."""
    app.dependency_overrides.clear()
    payload = {
        "token_address": "So11111111111111111111111111111111111111112",
        "trade_type": "buy",
        "amount_usdt": 100.0,
    }
    res = client.post("/api/trading/execute", json=payload)
    assert res.status_code == 401


def test_trading_wallet_initial_balance_is_10000():
    """Verify new user receives default virtual balance of 10,000 USDT."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-trader-uuid-1", "email": "trader@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # Reset to ensure clean initial state
        client.post("/api/trading/reset")

        res = client.get("/api/trading/wallet")
        assert res.status_code == 200
        data = res.json()
        assert data["balance_usdt"] == 10000.00
        assert data["total_portfolio_value_usdt"] == 10000.00
        assert data["total_pnl_usdt"] == 0.00
        assert isinstance(data["positions"], list)
        assert isinstance(data["recent_trades"], list)
    finally:
        app.dependency_overrides.clear()


def test_trading_execute_validation_errors():
    """Verify input validation rules for simulated trading."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-trader-uuid-1", "email": "trader@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # 1. Invalid trade type
        res1 = client.post(
            "/api/trading/execute",
            json={
                "token_address": "So11111111111111111111111111111111111111112",
                "trade_type": "hodl",
                "amount_usdt": 100.0,
            },
        )
        assert res1.status_code == 400
        assert "must be 'buy' or 'sell'" in res1.json()["detail"]

        # 2. Negative or zero amount
        res2 = client.post(
            "/api/trading/execute",
            json={
                "token_address": "So11111111111111111111111111111111111111112",
                "trade_type": "buy",
                "amount_usdt": -50.0,
            },
        )
        assert res2.status_code == 400
        assert "must be greater than zero" in res2.json()["detail"]

        # 3. Sell token without owning position
        mock_dex_data = {
            "found": True,
            "name": "Solana",
            "symbol": "SOL",
            "price_usd": 150.0,
        }
        with patch("zoe.tools.scanner.fetch_dexscreener_market_data", return_value=mock_dex_data):
            res3 = client.post(
                "/api/trading/execute",
                json={
                    "token_address": "MockNeverBoughtToken111111111111111111111",
                    "trade_type": "sell",
                    "amount_usdt": 100.0,
                },
            )
            assert res3.status_code == 400
            assert "do not hold any shares" in res3.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_trading_simulate_buy_and_sell_lifecycle():
    """Verify simulated BUY deducts balance and creates position, then SELL restores balance."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-trader-uuid-2", "email": "trader2@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    test_ca = "So11111111111111111111111111111111111111112"
    mock_dex_data = {
        "found": True,
        "name": "Solana",
        "symbol": "SOL",
        "price_usd": 200.0,
        "liquidity_usd": 50000000.0,
    }

    try:
        # Reset wallet
        client.post("/api/trading/reset")

        with patch("zoe.tools.scanner.fetch_dexscreener_market_data", return_value=mock_dex_data):
            # 1. Simulate BUY $1,000 USDT of SOL at $200
            res_buy = client.post(
                "/api/trading/execute",
                json={
                    "token_address": test_ca,
                    "trade_type": "buy",
                    "amount_usdt": 1000.0,
                    "token_name": "Solana",
                },
            )
            assert res_buy.status_code == 200
            buy_data = res_buy.json()
            assert buy_data["status"] == "success"
            assert buy_data["balance_usdt"] == 9000.00
            assert buy_data["trade"]["token_amount"] == 5.0  # 1000 / 200

            # 2. Check wallet positions
            res_wallet = client.get("/api/trading/wallet")
            assert res_wallet.status_code == 200
            wallet_data = res_wallet.json()
            assert wallet_data["balance_usdt"] == 9000.00
            assert len(wallet_data["positions"]) == 1
            pos = wallet_data["positions"][0]
            assert pos["token_address"] == test_ca
            assert pos["token_amount"] == 5.0
            assert pos["current_value_usdt"] == 1000.00

            # 3. Simulate SELL $500 USDT of position
            res_sell = client.post(
                "/api/trading/execute",
                json={
                    "token_address": test_ca,
                    "trade_type": "sell",
                    "amount_usdt": 500.0,
                    "token_name": "Solana",
                },
            )
            assert res_sell.status_code == 200
            sell_data = res_sell.json()
            assert sell_data["status"] == "success"
            assert sell_data["balance_usdt"] == 9500.00

            # 4. Check wallet after partial sell
            res_wallet2 = client.get("/api/trading/wallet")
            wallet_data2 = res_wallet2.json()
            assert wallet_data2["balance_usdt"] == 9500.00
            assert len(wallet_data2["positions"]) == 1
            assert round(wallet_data2["positions"][0]["token_amount"], 2) == 2.5
    finally:
        app.dependency_overrides.clear()


def test_trading_reset_wallet():
    """Verify reset endpoint purges positions and restores $10k virtual cash."""
    app.dependency_overrides.clear()
    mock_user = {"id": "test-trader-uuid-3", "email": "trader3@example.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        res = client.post("/api/trading/reset")
        assert res.status_code == 200
        assert res.json()["balance_usdt"] == 10000.00

        wallet_res = client.get("/api/trading/wallet")
        assert wallet_res.status_code == 200
        assert wallet_res.json()["balance_usdt"] == 10000.00
        assert len(wallet_res.json()["positions"]) == 0
    finally:
        app.dependency_overrides.clear()
