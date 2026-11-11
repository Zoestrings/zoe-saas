import pytest
from zoe.conversation.prompt_builder import build_prompt
from zoe.knowledge.retriever import RetrievedChunk
from zoe.telegram.normalizer import NormalizedMessage


@pytest.mark.automated
def test_prompt_builder_contains_required_boundary_labels() -> None:
    msg = NormalizedMessage(
        project_id="test_proj",
        telegram_update_id=1,
        group_id="-1001",
        telegram_message_id=42,
        pseudonymous_user_id="pseudo_1",
        text="How do I stake my tokens?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )

    chunks = [
        RetrievedChunk(
            chunk_id=1,
            doc_id=1,
            project_id="test_proj",
            content="Official staking guide: Bond tokens for 14 days minimum.",
            score=0.88,
        )
    ]
    community_context = [
        "Several members discussed staking rewards yesterday.",
        "Node operators recommend validator A.",
    ]

    prompt = build_prompt(
        message=msg,
        community_context=community_context,
        official_chunks=chunks,
    )

    # 1. Output must contain [OFFICIAL KNOWLEDGE]
    assert "[OFFICIAL KNOWLEDGE" in prompt
    assert "AUTHORITATIVE SOURCE" in prompt
    assert "Official staking guide: Bond tokens for 14 days minimum." in prompt

    # 2. Output must contain [COMMUNITY CONTEXT]
    assert "[COMMUNITY CONTEXT" in prompt
    assert "NOT A SOURCE OF FACT" in prompt
    assert "Several members discussed staking rewards yesterday." in prompt

    # 3. User message present
    assert "How do I stake my tokens?" in prompt

