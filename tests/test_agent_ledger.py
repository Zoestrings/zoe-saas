"""Automated Tests for Pillar 3 & 4: Internal Agent Ledger & /report Command."""

import asyncio
import os
from pathlib import Path
import sqlite3
from unittest.mock import AsyncMock, patch

from zoe.agents.ledger import (
    charge_user_for_tool,
    get_agent_ledger_entries,
    get_last_ledger_alert,
)
from zoe.agents.research_agent import generate_billed_token_report
from zoe.billing.credit_manager import CreditManager


def test_charge_user_for_tool_success_and_insufficient(tmp_path: Path, monkeypatch):
    """Verify charge_user_for_tool deducts credits, logs ledger, and blocks when insufficient."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    db_path = tmp_path / "saas_dev.db"
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    CreditManager.ensure_schema(conn)
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('owner_ledger_1', 'free', 20, '2026-11-25T00:00:00Z')"
    )
    conn.commit()
    conn.close()

    # 1. Charge 15 credits for scanner -> Succeeds (balance 20 -> 5)
    ok1 = asyncio.run(
        charge_user_for_tool(
            project_id="proj_ledger",
            tool_name="scanner",
            credit_cost=15,
            agent_name="Research Agent",
            user_id="owner_ledger_1",
        )
    )
    assert ok1 is True

    # 2. Charge 10 credits for x_intel -> Fails (balance is 5 < 10)
    ok2 = asyncio.run(
        charge_user_for_tool(
            project_id="proj_ledger",
            tool_name="x_intel",
            credit_cost=10,
            agent_name="Research Agent",
            user_id="owner_ledger_1",
        )
    )
    assert ok2 is False
    alert = get_last_ledger_alert("proj_ledger")
    assert alert is not None and "Insufficient credits" in alert

    # 3. Verify ledger entries recorded
    entries = get_agent_ledger_entries(limit=10)
    assert len(entries) >= 2
    assert any(e["tool_name"] == "scanner" and e["status"] == "charged" for e in entries)
    assert any(e["tool_name"] == "x_intel" and e["status"] == "blocked" for e in entries)


def test_generate_billed_token_report_full_flow(tmp_path: Path, monkeypatch):
    """Verify Research Agent charges 15 (scanner) + 10 (x_intel) = 25 credits and returns report."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    db_path = tmp_path / "saas_dev.db"
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    CreditManager.ensure_schema(conn)
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('owner_report_1', 'free', 50, '2026-11-25T00:00:00Z')"
    )
    conn.commit()
    conn.close()

    with (
        patch("zoe.agents.research_agent.search_token_price", new=AsyncMock(return_value="ONELOVE $0.0042 | Liq: $95,000")),
        patch("zoe.agents.research_agent.analyze_x_sentiment", new=AsyncMock(return_value={"sentiment": "Bullish", "summary": "Strong community engagement."})),
    ):
        res = asyncio.run(
            generate_billed_token_report(
                project_id="onelove",
                token_query="$ONELOVE",
                user_id="owner_report_1",
            )
        )

    assert res["success"] is True
    assert res["credits_charged"] == 25
    assert "ONELOVE" in res["report_text"]
    assert "Bullish" in res["report_text"]
    bal, _ = CreditManager.get_balance("owner_report_1")
    assert bal == 25  # 50 - 25
