"""Integration tests for the Dual-Input Multimodal Pipeline (Text + Voice Notes + Web Search)."""

from pathlib import Path
import faiss
import numpy as np
import pytest

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.telegram.normalizer import normalize_update_async
from zoe.worker.pipeline import process_message

PROJECT_ID = "p1"
GROUP_ID = "-100999"
HMAC_KEY = "test_hmac_secret_key_at_least_32_chars_long"


class MockEmbeddingModel:
    """Fast in-memory mock embedding model matching indexed vectors with high similarity."""

    def __init__(self, high_similarity: bool = True, dim: int = 384):
        self.high_similarity = high_similarity
        self.dim = dim

    def encode(self, texts, normalize_embeddings: bool = True):
        n = len(texts)
        if self.high_similarity:
            arr = np.ones((n, self.dim), dtype=np.float32)
        else:
            # Low similarity vector orthogonal to ones (dot product near 0)
            arr = np.zeros((n, self.dim), dtype=np.float32)
            arr[:, 0] = 1.0  # (1, 0, 0, ...) dot (1, 1, 1, ...) / sqrt(384) = 1/sqrt(384) ~ 0.051 < 0.35
        if normalize_embeddings:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms
        return arr


@pytest.fixture
def multimodal_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases with indexed documents."""
    # 1. Operational DB
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn_op.executescript(sql_op)
    conn_op.execute(
        "INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) "
        "VALUES ('p1', 'Hummingbird Test', '-100999', '{\"participation\": {\"respond_to_casual\": true}}', '2026-01-01 00:00:00', 1)"
    )
    conn_op.commit()

    # 2. Knowledge DB
    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_knowledge.sql").read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    conn_kb.execute(
        """
        INSERT INTO official_documents (id, project_id, filename, source_url, ingested_at, quarantined)
        VALUES (1, 'p1', 'hummingbird_staking.txt', 'https://hummingbirdco.io', '2026-01-01 00:00:00', 0)
        """
    )
    conn_kb.execute(
        """
        INSERT INTO official_chunks (id, doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (
            1, 1, 'p1', 0,
            'Hummingbird staking requires an unbonding period of exactly 14 days. Users earn $FLY tokens by securing the network.',
            20, 1
        )
        """
    )
    conn_kb.commit()

    # 3. Community Memory DB
    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_community_memory.sql").read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)
    conn_mem.commit()

    # 4. Build FAISS Index directly
    index_dir = tmp_path / "indexes"
    proj_idx_dir = index_dir / "p1"
    proj_idx_dir.mkdir(parents=True, exist_ok=True)

    base_index = faiss.IndexFlatIP(384)
    index = faiss.IndexIDMap2(base_index)
    vector = np.ones((1, 384), dtype=np.float32)
    vector = vector / np.linalg.norm(vector)
    index.add_with_ids(vector, np.array([1], dtype=np.int64))
    faiss.write_index(index, str(proj_idx_dir / "index.faiss"))

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }
    return conns, op_path, kb_path, mem_path, index_dir, tmp_path


@pytest.mark.anyio
async def test_a_typing_flows_through_rag(multimodal_env):
    """Test A (Typing): A standard typed text message flows through RAG successfully."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = multimodal_env
    conn_op = conns["operational"]

    # 1. Simulate incoming text update
    update = {
        "update_id": 1001,
        "message": {
            "message_id": 401,
            "date": 1730000000,
            "chat": {"id": -100999, "type": "supergroup"},
            "from": {"id": 111111, "is_bot": False, "username": "alice"},
            "text": "What is the unbonding period for Hummingbird staking?",
        },
    }

    # 2. Normalize standard text message
    norm_msg = await normalize_update_async(
        project_id=PROJECT_ID,
        update=update,
        configured_group_id=GROUP_ID,
        hmac_key=HMAC_KEY,
    )
    assert norm_msg is not None
    assert norm_msg.text == "What is the unbonding period for Hummingbird staking?"
    assert norm_msg.is_voice is False

    # 3. Persist to inbox
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """,
        (norm_msg.project_id, norm_msg.telegram_update_id, norm_msg.group_id, norm_msg.telegram_message_id, norm_msg.pseudonymous_user_id, norm_msg.text),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    # 4. Process through Unified Pipeline using mock embedding model with RAG match
    mock_llm = MockLLMClient(canned_response="The unbonding period for Hummingbird staking is 14 days.")
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        llm_client=mock_llm,
    )

    assert result.responded is True
    assert result.response_text == "The unbonding period for Hummingbird staking is 14 days."
    assert result.safety_result.is_safe is True

    # Confirm outbox response persisted
    res_row = conn_op.execute("SELECT text FROM responses WHERE trigger_message_id = 401").fetchone()
    assert res_row is not None
    assert "14 days" in res_row[0]


@pytest.mark.anyio
async def test_b_voice_transcribed_flows_through_rag(multimodal_env):
    """Test B (Voice): A mocked voice note is transcribed and flows through the exact same RAG pipeline."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = multimodal_env
    conn_op = conns["operational"]

    downloaded_files = []

    class MockVoiceAdapter:
        async def download_file(self, file_id, dest_path):
            p = Path(dest_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"mock_ogg_voice_payload_bytes")
            downloaded_files.append(p)
            return p

    def mock_whisper_transcriber(audio_file_path: Path) -> str:
        assert audio_file_path.exists()
        return "What is the unbonding period for Hummingbird staking?"

    # 1. Simulate incoming voice update
    update = {
        "update_id": 1002,
        "message": {
            "message_id": 402,
            "date": 1730000000,
            "chat": {"id": -100999, "type": "supergroup"},
            "from": {"id": 222222, "is_bot": False, "username": "bob"},
            "voice": {
                "file_id": "telegram_voice_file_xyz_789",
                "duration": 6,
                "mime_type": "audio/ogg",
            },
        },
    }

    # 2. Normalize voice message (downloads .ogg to tmp, transcribes, deletes .ogg)
    norm_msg = await normalize_update_async(
        project_id=PROJECT_ID,
        update=update,
        configured_group_id=GROUP_ID,
        hmac_key=HMAC_KEY,
        adapter=MockVoiceAdapter(),
        transcriber=mock_whisper_transcriber,
        tmp_dir=tmp_path / "data_tmp",
    )
    assert norm_msg is not None
    assert norm_msg.text == "What is the unbonding period for Hummingbird staking?"
    assert norm_msg.is_voice is True

    # Verify temp file was cleaned up (try/finally verified)
    assert len(downloaded_files) == 1
    assert not downloaded_files[0].exists()

    # 3. Persist to inbox
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """,
        (norm_msg.project_id, norm_msg.telegram_update_id, norm_msg.group_id, norm_msg.telegram_message_id, norm_msg.pseudonymous_user_id, norm_msg.text),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    # 4. Unified pipeline processes transcribed text identically to typing
    mock_llm = MockLLMClient(canned_response="The unbonding period for Hummingbird staking is 14 days.")
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        llm_client=mock_llm,
    )

    assert result.responded is True
    assert result.response_text == "The unbonding period for Hummingbird staking is 14 days."
    assert result.safety_result.is_safe is True


@pytest.mark.anyio
async def test_c_voice_web_search_fallback(multimodal_env):
    """Test C (Voice + Web): A mocked voice note asks a question not in RAG docs, triggering web search fallback."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = multimodal_env
    conn_op = conns["operational"]

    class MockVoiceAdapter:
        async def download_file(self, file_id, dest_path):
            p = Path(dest_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"mock_ogg_voice_payload_bytes")
            return p

    def mock_whisper_transcriber(audio_file_path: Path) -> str:
        return "Who won the latest Solana global hackathon grand prize?"

    # 1. Normalize voice message
    update = {
        "update_id": 1003,
        "message": {
            "message_id": 403,
            "date": 1730000000,
            "chat": {"id": -100999, "type": "supergroup"},
            "from": {"id": 333333, "is_bot": False, "username": "charlie"},
            "voice": {
                "file_id": "telegram_voice_file_web_search_456",
                "duration": 5,
            },
        },
    }

    norm_msg = await normalize_update_async(
        project_id=PROJECT_ID,
        update=update,
        configured_group_id=GROUP_ID,
        hmac_key=HMAC_KEY,
        adapter=MockVoiceAdapter(),
        transcriber=mock_whisper_transcriber,
        tmp_dir=tmp_path / "data_tmp",
    )
    assert norm_msg is not None
    assert norm_msg.text == "Who won the latest Solana global hackathon grand prize?"
    assert norm_msg.is_voice is True

    # 2. Persist to inbox
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """,
        (norm_msg.project_id, norm_msg.telegram_update_id, norm_msg.group_id, norm_msg.telegram_message_id, norm_msg.pseudonymous_user_id, norm_msg.text),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    # 3. Mock web search fallback
    web_search_called = []

    def mock_web_search(query: str):
        web_search_called.append(query)
        return [
            {
                "title": "Solana Renaissance Hackathon Winners Announced",
                "body": "Ore was awarded the Grand Prize at the Solana Renaissance Hackathon.",
                "href": "https://solana.com/news/renaissance-hackathon-winners",
            }
        ]

    # LLM mock verifies it receives the web results
    class WebAwareMockLLMClient:
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            assert "[WEB SEARCH RESULTS" in user_prompt
            assert "Solana Renaissance Hackathon" in user_prompt
            return "Ore won the Grand Prize at the Solana Renaissance Hackathon according to recent announcements."

    # Using high_similarity=False so RAG returns score ~ 0.051 < 0.35, triggering fallback
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=False),
        llm_client=WebAwareMockLLMClient(),
        web_search_fn=mock_web_search,
    )

    assert result.responded is True
    assert len(web_search_called) == 1
    assert "Solana global hackathon" in web_search_called[0]
    assert "Ore won the Grand Prize" in result.response_text
    assert result.safety_result.is_safe is True


@pytest.mark.anyio
async def test_pipeline_smart_routing_bitcoin_price_to_web_search(multimodal_env):
    """Verify 'What is the price of Bitcoin?' routes to web search and injects live price data."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = multimodal_env
    conn_op = conns["operational"]

    update = {
        "update_id": 1004,
        "message": {
            "message_id": 404,
            "date": 1730000000,
            "chat": {"id": -100999, "type": "supergroup"},
            "from": {"id": 444444, "is_bot": False, "username": "dan"},
            "text": "What is the price of Bitcoin?",
        },
    }

    norm_msg = await normalize_update_async(
        project_id=PROJECT_ID,
        update=update,
        configured_group_id=GROUP_ID,
        hmac_key=HMAC_KEY,
    )
    assert norm_msg is not None

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """,
        (norm_msg.project_id, norm_msg.telegram_update_id, norm_msg.group_id, norm_msg.telegram_message_id, norm_msg.pseudonymous_user_id, norm_msg.text),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    web_search_calls = []

    def mock_web_search(query: str):
        web_search_calls.append(query)
        return [
            {
                "title": "Bitcoin Price Today | BTC to USD",
                "body": "The live price of Bitcoin is $88,450.00 USD with a 24-hour trading volume.",
                "href": "https://coinmarketcap.com/currencies/bitcoin/",
            }
        ]

    class BitcoinPriceMockLLMClient:
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            assert "[WEB SEARCH RESULTS" in user_prompt
            assert "$88,450.00" in user_prompt
            return "Bitcoin is currently trading at around $88,450 USD according to recent market data."

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=False),
        llm_client=BitcoinPriceMockLLMClient(),
        web_search_fn=mock_web_search,
    )

    assert result.responded is True
    assert len(web_search_calls) == 1
    assert "Bitcoin" in web_search_calls[0]
    assert "$88,450" in result.response_text
    assert result.safety_result.is_safe is True
