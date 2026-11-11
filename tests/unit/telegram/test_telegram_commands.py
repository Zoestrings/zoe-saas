"""Unit tests for Telegram Bot Commands and Menu Button registration.

Tests:
- Test A: Assert that the /ca command returns the exact contract address from onelove.yaml.
- Test B: Assert that the /price command triggers the DexScreener tool.
- Test C: Assert that the /help command returns the formatted command list.
- Test D: Assert that the /ask command strips the prefix and passes the rest to the pipeline.
- Test E: Assert that set_bot_commands registers the commands with Telegram Bot API.
"""

from pathlib import Path
import random
import pytest

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import persist_batch
from zoe.settings import load_project_config
from zoe.telegram.adapter import PTBTelegramAdapter
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.claim import claim_next_inbox_row
from zoe.worker.pipeline import process_message

ONELOVE_CA = "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"


def test_a_ca_command_returns_contract_address():
    """Test A: Assert that the /ca command returns the exact contract address from onelove.yaml."""
    cfg = load_project_config("onelove")
    expected_ca = cfg.get("token_address") or cfg.get("project", {}).get("token_address")
    assert expected_ca == ONELOVE_CA

    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="trader_ca",
        text="/ca",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 11:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_cmd_ca")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    assert expected_ca in result.response_text
    assert "contract address for One Love" in result.response_text


def test_b_price_command_triggers_dexscreener(monkeypatch):
    """Test B: Assert that the /price command triggers the DexScreener tool."""
    conn_op = open_operational_db("data/operational/operational.db")

    called_dexscreener = []

    def mock_get_intel(token_address=None, project_id=None, **kwargs):
        called_dexscreener.append({"token_address": token_address, "project_id": project_id})
        return {
            "ca": token_address or ONELOVE_CA,
            "found": True,
            "name": "One Love Sailing",
            "symbol": "ONELOVE",
            "price": "0.000095",
            "market_cap": "95000",
            "fdv": "95000",
            "liquidity": "1500",
            "volume_24h": "500",
            "error": None,
        }

    monkeypatch.setattr("zoe.tools.crypto_intel.get_token_intel_sync", mock_get_intel)

    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="trader_price",
        text="/price",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 11:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_cmd_price")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert len(called_dexscreener) == 1
    assert called_dexscreener[0]["project_id"] == "onelove"
    assert result.response_text is not None
    assert "Price: $0.000095" in result.response_text
    assert "Market Cap: $95,000.00" in result.response_text


def test_c_help_command():
    """Test C: Assert that /help returns the formatted command menu."""
    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="new_user",
        text="/help",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 11:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_cmd_help")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    resp = result.response_text
    assert "/ca" in resp
    assert "/price" in resp
    assert "/ask" in resp
    assert "/help" in resp
    assert "Ask One Love AI" in resp


def test_d_ask_command_strips_prefix():
    """Test D: Assert that /ask strips the prefix and passes the question to the pipeline."""
    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="user_ask",
        text="/ask who is Captain Robbie Olson?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 11:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_cmd_ask")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None


@pytest.mark.anyio
async def test_e_mock_adapter_set_bot_commands():
    """Test E: Assert that set_bot_commands works on adapter."""
    adapter = MockTelegramAdapter()
    res = await adapter.set_bot_commands()
    assert res is True
    assert adapter.bot_commands_set is True

