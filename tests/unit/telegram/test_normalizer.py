import pytest

from zoe.telegram.normalizer import (
    NormalizedMessage,
    compute_pseudonym,
    normalize_update,
)
from zoe.utils.errors import ChatMigrationAlert

PROJECT_ID = "test_project"
GROUP_ID = "-1001234567890"
HMAC_KEY = "test_super_secret_hmac_key"
RAW_USER_ID = 987654321


def make_valid_update(text: str = "Hello Zoe!", user_id: int = RAW_USER_ID, **kwargs) -> dict:
    message = {
        "message_id": 42,
        "date": 1700000000,
        "chat": {"id": int(GROUP_ID), "type": "supergroup"},
        "from": {"id": user_id, "is_bot": False, "first_name": "Alice"},
        "text": text,
    }
    message.update(kwargs)
    return {
        "update_id": 1001,
        "message": message,
    }


@pytest.mark.automated
def test_normalizer_produces_normalized_message() -> None:
    update = make_valid_update()
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)

    assert msg is not None
    assert isinstance(msg, NormalizedMessage)
    assert msg.project_id == PROJECT_ID
    assert msg.telegram_update_id == 1001
    assert msg.group_id == GROUP_ID
    assert msg.telegram_message_id == 42
    assert msg.text == "Hello Zoe!"
    assert msg.is_forward is False
    assert msg.reply_to_message_id is None
    assert msg.pseudonymous_user_id == compute_pseudonym(RAW_USER_ID, HMAC_KEY)
    assert str(RAW_USER_ID) not in msg.pseudonymous_user_id


@pytest.mark.automated
def test_normalizer_discards_bot_message() -> None:
    update = make_valid_update()
    update["message"]["from"]["is_bot"] = True
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is None


@pytest.mark.automated
def test_normalizer_discards_wrong_chat() -> None:
    update = make_valid_update()
    update["message"]["chat"]["id"] = -1009999999999
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is None


@pytest.mark.automated
def test_normalizer_discards_edited_message() -> None:
    update = {
        "update_id": 1002,
        "edited_message": {
            "message_id": 42,
            "date": 1700000000,
            "chat": {"id": int(GROUP_ID)},
            "from": {"id": RAW_USER_ID, "is_bot": False},
            "text": "Edited text",
        },
    }
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is None


@pytest.mark.automated
def test_normalizer_discards_media() -> None:
    # Test discarding photo, video, sticker, document (voice is handled separately)
    for media_type in ["photo", "video", "sticker", "document"]:
        update = make_valid_update(text="Media caption")
        update["message"][media_type] = [{"file_id": "xyz"}] if media_type == "photo" else {"file_id": "xyz"}
        msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
        assert msg is None, f"Expected media '{media_type}' to be discarded"


@pytest.mark.automated
def test_normalizer_processes_voice_note() -> None:
    update = make_valid_update(text=None)
    update["message"].pop("text", None)
    update["message"]["voice"] = {
        "file_id": "voice_file_123",
        "duration": 4,
        "transcription": "What is Hummingbird tokenomics?",
    }
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is not None
    assert msg.text == "What is Hummingbird tokenomics?"
    assert msg.is_voice is True


@pytest.mark.anyio
async def test_normalizer_processes_voice_note_async(tmp_path) -> None:
    from zoe.telegram.normalizer import normalize_update_async

    class MockVoiceAdapter:
        async def download_file(self, file_id, dest_path):
            dest_path.write_bytes(b"dummy ogg audio data")
            return dest_path

    update = make_valid_update(text=None)
    update["message"].pop("text", None)
    update["message"]["voice"] = {
        "file_id": "voice_file_abc",
        "duration": 5,
    }

    mock_transcriber = lambda path: "How does staking work on Hummingbird?"
    msg = await normalize_update_async(
        PROJECT_ID,
        update,
        GROUP_ID,
        HMAC_KEY,
        adapter=MockVoiceAdapter(),
        transcriber=mock_transcriber,
        tmp_dir=tmp_path,
    )
    assert msg is not None
    assert msg.text == "How does staking work on Hummingbird?"
    assert msg.is_voice is True


@pytest.mark.automated
def test_normalizer_retains_forwarded_text() -> None:
    update = make_valid_update(text="This was forwarded", forward_date=1700000000)
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is not None
    assert msg.text == "This was forwarded"
    assert msg.is_forward is True


@pytest.mark.automated
def test_normalizer_retains_bot_command() -> None:
    update = make_valid_update(text="/start")
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is not None
    assert msg.text == "/start"
    assert msg.is_forward is False


@pytest.mark.automated
def test_normalizer_raises_on_migration() -> None:
    update = make_valid_update(migrate_to_chat_id=-1009876543210)
    with pytest.raises(ChatMigrationAlert) as exc_info:
        normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert "-1009876543210" in str(exc_info.value)


@pytest.mark.automated
def test_no_raw_telegram_id_in_normalized_message() -> None:
    update = make_valid_update(user_id=12345678)
    msg = normalize_update(PROJECT_ID, update, GROUP_ID, HMAC_KEY)
    assert msg is not None

    # Check all fields of the dataclass: raw user ID must not appear anywhere
    for field_name in msg.__dataclass_fields__:
        val = getattr(msg, field_name)
        assert val != 12345678
        assert str(val) != "12345678"


@pytest.mark.automated
def test_pseudonym_is_stable() -> None:
    user_id = 5544332211
    pseudo1 = compute_pseudonym(user_id, HMAC_KEY)
    pseudo2 = compute_pseudonym(user_id, HMAC_KEY)
    assert pseudo1 == pseudo2

    diff_key = "different_secret_key"
    pseudo3 = compute_pseudonym(user_id, diff_key)
    assert pseudo1 != pseudo3

