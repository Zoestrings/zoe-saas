"""Tests for Web3 Live News Intelligence Tool and Pipeline Integration."""

import asyncio
import pytest
from unittest.mock import patch

from zoe.conversation.router import route_intent, extract_crypto_news_target
from zoe.tools.crypto_news import fetch_crypto_news_sync, fetch_crypto_news
from zoe.db.connections import (
    open_operational_db,
    open_official_knowledge_db,
    open_community_memory_db,
)
from zoe.worker.pipeline import process_message
from zoe.llm.mock import MockLLMClient
from zoe.participation.decision import ParticipationDecision


def test_router_crypto_news_intent():
    """Verify router categorizes news questions to crypto_news with accurate targets."""
    queries = [
        ("What's the latest news on XRP?", "crypto_news", "XRP"),
        ("Any crypto news today?", "crypto_news", "crypto"),
        ("What's happening with Solana?", "crypto_news", "SOLANA"),
        ("Did Bitcoin break ATH?", "crypto_news", "BITCOIN"),
        ("What is the latest breaking news about Ethereum?", "crypto_news", "ETHEREUM"),
        ("What's going on with Doge?", "crypto_news", "DOGE"),
    ]

    for q, expected_intent, expected_target in queries:
        assert route_intent(q) == expected_intent, f"Failed for query: {q}"
        assert extract_crypto_news_target(q) == expected_target, f"Target mismatch for: {q}"


def test_fetch_crypto_news_mocked():
    """Test fetch_crypto_news returns structured articles."""
    fake_items = [
        {
            "title": "SEC drops appeal against Ripple",
            "snippet": "The SEC has formally dismissed its appeal in the ongoing Ripple litigation.",
            "url": "https://coindesk.com/sec-ripple",
            "date": "2 hours ago",
            "source": "CoinDesk",
        },
        {
            "title": "XRP Ledger upgrade goes live on mainnet",
            "snippet": "New automated market maker features activated on XRPL.",
            "url": "https://u.today/xrpl-live",
            "date": "5 hours ago",
            "source": "U.Today",
        },
    ]

    with patch("zoe.tools.crypto_news._fetch_from_duckduckgo", return_value=fake_items):
        results = asyncio.run(fetch_crypto_news("XRP"))
        assert len(results) == 2
        assert results[0]["source"] == "CoinDesk"
        assert results[0]["title"] == "SEC drops appeal against Ripple"
        assert results[1]["url"] == "https://u.today/xrpl-live"


def test_pipeline_crypto_news_prompt_includes_sources(tmp_path):
    """Test pipeline incorporates source URLs and timestamps into the LLM prompt."""
    fake_news = [
        {
            "title": "SEC drops appeal against Ripple",
            "snippet": "The SEC has dismissed appeal in Ripple lawsuit.",
            "url": "https://coindesk.com/sec-ripple-dismiss",
            "date": "2 hours ago",
            "source": "CoinDesk",
        },
        {
            "title": "Institutional inflows hit $15M",
            "snippet": "Major institutional investors poured millions into XRP investment products.",
            "url": "https://cointelegraph.com/inflows-15m",
            "date": "1 day ago",
            "source": "CoinTelegraph",
        },
    ]

    conn_op = open_operational_db(tmp_path / "op.db")
    conn_kb = open_official_knowledge_db(tmp_path / "kb.db")
    conn_mem = open_community_memory_db(tmp_path / "mem.db")

    conn_op.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('test_proj', 'Test AI', '-100123', '{}', '2026-11-23T12:00:00Z', 1)
        """
    )
    conn_op.execute(
        """
        INSERT INTO inbox_messages (
            id, project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, state, state_changed_at, message_timestamp, created_at
        ) VALUES (1, 'test_proj', 101, '-100123', 201, 'user_1', "What's the latest news on XRP?", 'message_persisted', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z')
        """
    )
    conn_op.commit()

    mock_llm = MockLLMClient()
    inbox_row = {
        "id": 1,
        "project_id": "test_proj",
        "telegram_update_id": 101,
        "group_id": -100123,
        "telegram_message_id": 201,
        "pseudonymous_user_id": "user_1",
        "text": "What's the latest news on XRP?",
        "message_timestamp": "2026-11-23T12:00:00Z",
        "state": "message_persisted",
    }

    with patch("zoe.worker.pipeline.fetch_crypto_news_sync", return_value=fake_news):
        with patch("zoe.worker.pipeline.should_respond") as mock_should:
            mock_should.return_value = ParticipationDecision(decision="respond", should_respond=True, reason="direct_mention")

            res = process_message(
                inbox_row=inbox_row,
                db_conns={"operational": conn_op, "knowledge": conn_kb, "community": conn_mem, "memory": conn_mem},
                llm_client=mock_llm,
            )

            assert res.responded is True
            # Verify the LLM was called and prompt contained sources
            assert len(mock_llm.calls) > 0
            call_prompt = mock_llm.calls[-1]["user_prompt"]
            assert "https://coindesk.com/sec-ripple-dismiss" in call_prompt
            assert "CoinDesk" in call_prompt
            assert "CoinTelegraph" in call_prompt
            assert "https://cointelegraph.com/inflows-15m" in call_prompt
            assert "[TARGET ASSET]: XRP" in call_prompt


def test_pipeline_crypto_news_empty_fallback(tmp_path):
    """Test pipeline returns exact fallback message when no news is found without hallucinating."""
    conn_op = open_operational_db(tmp_path / "op.db")
    conn_kb = open_official_knowledge_db(tmp_path / "kb.db")
    conn_mem = open_community_memory_db(tmp_path / "mem.db")

    conn_op.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('test_proj', 'Test AI', '-100123', '{}', '2026-11-23T12:00:00Z', 1)
        """
    )
    conn_op.execute(
        """
        INSERT INTO inbox_messages (
            id, project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, state, state_changed_at, message_timestamp, created_at
        ) VALUES (2, 'test_proj', 102, '-100123', 202, 'user_1', "What's happening with Solana?", 'message_persisted', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z')
        """
    )
    conn_op.commit()

    mock_llm = MockLLMClient()
    inbox_row = {
        "id": 2,
        "project_id": "test_proj",
        "telegram_update_id": 102,
        "group_id": -100123,
        "telegram_message_id": 202,
        "pseudonymous_user_id": "user_1",
        "text": "What's happening with Solana?",
        "message_timestamp": "2026-11-23T12:00:00Z",
        "state": "message_persisted",
    }

    with patch("zoe.worker.pipeline.fetch_crypto_news_sync", return_value=[]):
        with patch("zoe.worker.pipeline.should_respond") as mock_should:
            mock_should.return_value = ParticipationDecision(decision="respond", should_respond=True, reason="direct_mention")

            res = process_message(
                inbox_row=inbox_row,
                db_conns={"operational": conn_op, "knowledge": conn_kb, "community": conn_mem, "memory": conn_mem},
                llm_client=mock_llm,
            )

            assert res.responded is True
            # Crucial: Exact fallback string returned without hallucinating
            cur = conn_op.execute("SELECT text FROM outbox_messages WHERE inbox_message_id = 2")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "I couldn't find any recent news for that asset."
            assert len(mock_llm.calls) == 0


def test_pipeline_crypto_news_provider_error_fallback(tmp_path):
    """Test pipeline returns graceful message when all news providers are down."""
    conn_op = open_operational_db(tmp_path / "op.db")
    conn_kb = open_official_knowledge_db(tmp_path / "kb.db")
    conn_mem = open_community_memory_db(tmp_path / "mem.db")

    conn_op.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('test_proj', 'Test AI', '-100123', '{}', '2026-11-23T12:00:00Z', 1)
        """
    )
    conn_op.execute(
        """
        INSERT INTO inbox_messages (
            id, project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, state, state_changed_at, message_timestamp, created_at
        ) VALUES (3, 'test_proj', 103, '-100123', 203, 'user_1', "Any crypto news today?", 'message_persisted', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z', '2026-11-23T12:00:00Z')
        """
    )
    conn_op.commit()

    mock_llm = MockLLMClient()
    inbox_row = {
        "id": 3,
        "project_id": "test_proj",
        "telegram_update_id": 103,
        "group_id": -100123,
        "telegram_message_id": 203,
        "pseudonymous_user_id": "user_1",
        "text": "Any crypto news today?",
        "message_timestamp": "2026-11-23T12:00:00Z",
        "state": "message_persisted",
    }

    with patch("zoe.worker.pipeline.fetch_crypto_news_sync", side_effect=Exception("API Connection Failure")):
        with patch("zoe.worker.pipeline.should_respond") as mock_should:
            mock_should.return_value = ParticipationDecision(decision="respond", should_respond=True, reason="direct_mention")

            res = process_message(
                inbox_row=inbox_row,
                db_conns={"operational": conn_op, "knowledge": conn_kb, "community": conn_mem, "memory": conn_mem},
                llm_client=mock_llm,
            )

            assert res.responded is True
            cur = conn_op.execute("SELECT text FROM outbox_messages WHERE inbox_message_id = 3")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "My live news providers are currently unavailable. Please check official sources."
            assert len(mock_llm.calls) == 0
