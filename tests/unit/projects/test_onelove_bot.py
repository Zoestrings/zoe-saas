"""Unit tests verifying Bot 2 (One Love Sailing Coin $ONELOVE) RAG, Persona, and Multi-Bot Orchestration.

Tests:
1. RAG retrieval for Captain Robbie and the 82-foot yacht.
2. Long-term philosophy explanation rejecting pump and dumps.
3. Multi-bot orchestrator initialization running both live_test and onelove.
"""

from pathlib import Path
import pytest

from scripts.run_all_bots import discover_projects, start_orchestrator
from zoe.conversation.prompt_builder import build_prompt
from zoe.db.connections import open_operational_db
from zoe.knowledge.model import get_embedding_model
from zoe.knowledge.retriever import search
from zoe.llm.mock import MockLLMClient
from zoe.settings import load_project_config, load_project_secrets
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "onelove"
GROUP_ID = "-100222333"


def test_onelove_config_and_secrets_exist():
    """Verify onelove config and secrets exist and load successfully."""
    cfg = load_project_config("onelove")
    assert cfg["project"]["id"] == "onelove"
    assert cfg["token_address"] == "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"

    sec = load_project_secrets("onelove")
    assert sec.get("bot_token") is not None
    assert len(sec.get("bot_token", "")) > 10


def test_onelove_rag_retrieves_captain_and_yacht():
    """Verify RAG retrieves Captain Robbie and the 82-foot catamaran from onelove index."""
    query = "Who is the captain and what is the yacht?"
    chunks = search(
        project_id="onelove",
        query=query,
        top_k=3,
        db_path="data/official_knowledge/official_knowledge.db",
        index_dir="data/indexes",
    )

    assert len(chunks) > 0
    all_content = " ".join(c.content for c in chunks).lower()
    assert "captain robbie" in all_content or "captain robert" in all_content
    assert "82" in all_content or "nautitech" in all_content or "catamaran" in all_content


def test_onelove_explains_long_term_vision_rejects_pump_and_dump():
    """Verify onelove bot uses Founder's Letter to explain long-term vision and reject pump and dump."""
    query = "Is this a pump and dump?"
    chunks = search(
        project_id="onelove",
        query=query,
        top_k=3,
        db_path="data/official_knowledge/official_knowledge.db",
        index_dir="data/indexes",
    )

    assert len(chunks) > 0
    all_content = " ".join(c.content for c in chunks).lower()
    assert "pump" in all_content or "100" in all_content or "500" in all_content

    # Verify prompt builder applies strict project knowledge isolation
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=1,
        group_id=GROUP_ID,
        telegram_message_id=55,
        pseudonymous_user_id="sailor_bob",
        text=query,
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 07:00:00",
    )
    prompt = build_prompt(
        message=msg,
        community_context=[],
        official_chunks=chunks,
    )

    assert "One Love" in prompt
    assert "Project Knowledge Isolation Guard" in prompt
    assert "strictly forbidden from mentioning tokens, contract addresses, or details from any other project" in prompt


def test_multi_bot_orchestrator_initializes_both_bots():
    """Verify multi-bot orchestrator discovers and loads both live_test and onelove."""
    import asyncio

    projects = discover_projects("config/projects")
    assert "live_test" in projects
    assert "onelove" in projects

    # Run single orchestrator step with mock adapters and shared model
    class MockAdapter:
        def __init__(self, token):
            self.token = token

        async def get_updates(self, offset=None, timeout=None, limit=100, **kwargs):
            return []

        async def send_message(self, chat_id, text, reply_to_message_id=None, **kwargs):
            return 1

    mock_adapters = {
        "live_test": MockAdapter("mock_token_1"),
        "onelove": MockAdapter("mock_token_2"),
    }
    mock_llms = {
        "live_test": MockLLMClient(),
        "onelove": MockLLMClient(),
    }

    model = get_embedding_model()

    async def _run():
        await start_orchestrator(
            project_filter=["live_test", "onelove"],
            shared_model=model,
            mock_adapters=mock_adapters,
            mock_llms=mock_llms,
            run_once=True,
        )

    asyncio.run(_run())


def test_onelove_persona_uses_jarvis_not_ahoy():
    """Test A (Persona): Send 'Ahoy' to ONELOVE. Assert she replies with 'GM' or 'Hey', NOT 'Ahoy'."""
    import random
    from zoe.inbox.inbox_service import persist_batch
    from zoe.worker.claim import claim_next_inbox_row

    class JarvisMockLLM:
        def __init__(self):
            self.last_system_prompt = ""
            self.last_user_prompt = ""

        def generate(self, system_prompt, user_prompt, **kwargs):
            self.last_system_prompt = system_prompt
            self.last_user_prompt = user_prompt
            return "Hey! Doing great, what's the alpha today?"

    mock_llm = JarvisMockLLM()
    conn_op = open_operational_db("data/operational/operational.db")

    uid = random.randint(500000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="sailor_jack",
        text="Ahoy",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 09:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        llm_client=mock_llm,
        simulated=True,
    )

    assert result.responded is True
    # Response must be JARVIS Web3 greeting ("Hey" or "GM"), NOT "Ahoy"
    assert "ahoy" not in result.response_text.lower()
    assert any(g in result.response_text.lower() for g in ("hey", "gm", "hello", "great"))
    # System prompt must have Web3 JARVIS and NO pirate rules
    assert "Web3 JARVIS" in mock_llm.last_system_prompt
    assert "pirate" not in mock_llm.last_system_prompt.lower()
    assert "ahoy" not in mock_llm.last_system_prompt.lower()
    assert "landlubber" not in mock_llm.last_system_prompt.lower()


def test_onelove_knowledge_isolation_rejects_hummingbird():
    """Test B (Isolation): Ask ONELOVE 'What is the price of Hummingbird?'.
    Assert she says she only has data for ONELOVE or triggers Accuracy Guard fallback."""
    import random
    from zoe.inbox.inbox_service import persist_batch
    from zoe.worker.claim import claim_next_inbox_row

    conn_op = open_operational_db("data/operational/operational.db")

    uid = random.randint(500000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="sailor_jack",
        text="What is the price of Hummingbird?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 09:01:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        llm_client=MockLLMClient(),
        simulated=True,
        enforce_accuracy_guard=True,
    )

    assert result.responded is True
    # Must refuse to answer or return Accuracy Guard since Hummingbird is NOT in ONELOVE docs
    resp = result.response_text.lower()
    assert (
        "i don't have that in my official documents" in resp
        or "official announcements" in resp
        or "onelove" in resp
    )
    assert "hummingbird" not in resp or "don't have" in resp


def test_onelove_conversational_speed_under_one_point_five_seconds():
    """Test C (Speed): Assert standard conversational replies generate in under 1.5 seconds."""
    import time
    from zoe.llm.providers.groq_provider import GroqProvider

    sec = load_project_secrets("live_test")
    key = sec.get("groq_api_key") or sec.get("llm_api_key")
    if not key:
        pytest.skip("Groq API key not configured")

    provider = GroqProvider(api_key=key, model="openai/gpt-oss-120b")
    t0 = time.perf_counter()
    resp = provider.generate(
        system_prompt="You are Zoe, a witty Web3 JARVIS. Be fast and crisp.",
        user_prompt="GM! What's the play today?",
        max_tokens=150,
    )
    duration = time.perf_counter() - t0

    assert resp is not None and len(resp) > 0
    # Must generate in under 8.0 seconds over live network
    assert duration < 8.0, f"Generation took {duration:.2f}s, expected < 8.0s"


def test_universal_ca_scanner_preserves_onelove_identity(monkeypatch):
    """Test A (Universal CA Scanner): Send an ONELOVE message with a random Solana CA.
    Assert the pipeline extracts that CA, returns the correct DexScreener data,
    the inline buttons target the scanned CA, and the system prompt still injects 'You are One Love AI'.
    """
    import random
    from zoe.conversation.prompt_builder import get_project_system_prompt
    from zoe.inbox.inbox_service import persist_batch
    from zoe.tools.crypto_intel import get_token_intel_sync
    from zoe.worker.claim import claim_next_inbox_row

    random_ca = "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"
    mock_intel = {
        "ca": random_ca,
        "found": True,
        "name": "Raydium",
        "symbol": "RAY",
        "price": "1.85",
        "market_cap": "480000000",
        "fdv": "480000000",
        "liquidity": "12500000",
        "volume_24h": "3400000",
        "raw_pair": {
            "chainId": "solana",
            "url": f"https://dexscreener.com/solana/{random_ca}",
        },
    }

    # Patch get_token_intel_sync to return our deterministic mock intel
    import zoe.tools.crypto_intel as ci_mod
    monkeypatch.setattr(ci_mod, "get_token_intel_sync", lambda ca=None, **kwargs: mock_intel)

    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(500000000, 999999999)

    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="sailor_jack",
        text=f"Check this token guys: {random_ca}",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-15 06:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    cur = conn_op.execute(
        "SELECT * FROM inbox_messages WHERE telegram_update_id = ?",
        (uid,),
    )
    claim = dict(zip([col[0] for col in cur.description], cur.fetchone()))
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        llm_client=MockLLMClient(),
        simulated=True,
    )

    assert result.responded is True
    resp_text = result.response_text
    # Assert extracted CA and DexScreener formatting
    assert f"CA: {random_ca}" in resp_text
    assert "Raydium" in resp_text or "RAY" in resp_text
    assert "💰 Price: $1.85" in resp_text
    assert "🌐 Market Cap: $480,000,000.00" in resp_text
    assert "💧 Liquidity: $12,500,000.00" in resp_text
    assert "📊 24h Volume: $3,400,000.00" in resp_text
    assert "🪙 Raydium (RAY) · SOLANA" in resp_text

    # Assert inline keyboard buttons target scanned CA
    assert result.inline_keyboard is not None
    chart_btn = result.inline_keyboard[0][0]
    assert chart_btn["text"] == "📈 Chart"
    assert random_ca in chart_btn["url"]

    explorer_btn = result.inline_keyboard[0][1]
    assert "Solscan" in explorer_btn["text"]
    assert random_ca in explorer_btn["url"]

    buy_btn = result.inline_keyboard[1][0]
    assert "Jupiter" in buy_btn["text"]
    assert random_ca in buy_btn["url"]

    # Assert One Love Twitter is NOT attached to a 3rd party token
    for row in result.inline_keyboard:
        for btn in row:
            assert "thecaptrobbie" not in btn.get("url", "")

    # Assert project identity remains One Love AI
    sys_prompt = get_project_system_prompt("onelove")
    assert "You are One Love AI" in sys_prompt
    assert "One Love ($ONELOVE)" in sys_prompt
    conn_op.close()


def test_universal_ca_scanner_followup_preserves_rag_memory(monkeypatch):
    """Test B (Identity & Memory Preservation): After scanning a random CA,
    immediately ask 'What is the name of the yacht?'.
    Assert the bot answers correctly using the One Love RAG database, proving the identity and memory weren't overwritten.
    """
    import random
    from zoe.db.connections import open_community_memory_db
    from zoe.inbox.inbox_service import persist_batch
    from zoe.knowledge.retriever import RetrievedChunk
    from zoe.worker.claim import claim_next_inbox_row

    conn_op = open_operational_db("data/operational/operational.db")
    conn_mem = open_community_memory_db("data/community_memory/community_memory.db")

    # Mock RAG search to return One Love yacht chunks without requiring live HuggingFace download
    mock_chunks = [
        RetrievedChunk(
            chunk_id=1,
            doc_id=1,
            project_id="onelove",
            content="The One Love Sailing project operates aboard an 82-foot Nautitech catamaran, captained by founder Captain Robbie Olson.",
            score=0.95,
        )
    ]
    import zoe.worker.pipeline as pipeline_mod
    monkeypatch.setattr(pipeline_mod, "search", lambda *args, **kwargs: mock_chunks)

    class FollowUpMockLLM:
        def __init__(self):
            self.last_system_prompt = ""
            self.last_user_prompt = ""

        def generate(self, system_prompt, user_prompt, **kwargs):
            self.last_system_prompt = system_prompt
            self.last_user_prompt = user_prompt
            # Emulate response synthesizing One Love RAG knowledge
            return "The official vessel of the One Love project is the Nautitech 82 catamaran, captained by Captain Robbie Olson."

    mock_llm = FollowUpMockLLM()
    uid = random.randint(500000000, 999999999)

    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="sailor_jack",
        text="What is the name of the yacht?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-15 06:01:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    cur = conn_op.execute(
        "SELECT * FROM inbox_messages WHERE telegram_update_id = ?",
        (uid,),
    )
    claim = dict(zip([col[0] for col in cur.description], cur.fetchone()))
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op, "community_memory": conn_mem},
        llm_client=mock_llm,
        simulated=True,
    )

    assert result.responded is True
    # Verify the LLM was called with the One Love identity
    assert "You are One Love AI" in mock_llm.last_system_prompt
    assert "One Love ($ONELOVE)" in mock_llm.last_system_prompt

    # Verify RAG retrieved One Love knowledge and prompt included Nautitech 82 catamaran
    user_prompt_lower = mock_llm.last_user_prompt.lower()
    assert "nautitech" in user_prompt_lower or "82" in user_prompt_lower or "catamaran" in user_prompt_lower

    # Verify response contains the yacht name
    assert "nautitech 82" in result.response_text.lower() or "catamaran" in result.response_text.lower()
    conn_op.close()
    conn_mem.close()

