import copy
from pathlib import Path
import pytest
import yaml

from zoe.settings import validate_config
from zoe.utils.errors import ConfigError

BASE_CONFIG = {
    "project": {
        "id": "live_test",
        "name": "Live Test",
        "description": "Test",
        "version": "0.1.0",
        "created_at": "2026-11-05 00:00:00",
        "active": 1,
    },
    "telegram": {
        "environment": "live_verification",
        "group_id": "-1001234567890",
        "live_send_responses_enabled": True,
        "live_send_moderator_notifications_enabled": True,
        "poll_timeout_seconds": 30,
        "poll_interval_seconds": 1,
    },
}

BASE_SECRETS = {
    "bot_token": "123456:FAKE_TOKEN",
    "hmac_key": "some_secret_key_32_characters_min",
}


def test_startup_validation_passes_when_evidence_valid(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)

    # Valid PROVIDER_APPROVAL.md
    (docs_dir / "PROVIDER_APPROVAL.md").write_text(
        yaml.safe_dump({
            "provider_approval": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    # Valid LIVE_SEND_VERIFICATION.md
    (docs_dir / "LIVE_SEND_VERIFICATION.md").write_text(
        yaml.safe_dump({
            "live_send_verification": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    # Should not raise
    validate_config(copy.deepcopy(BASE_CONFIG), copy.deepcopy(BASE_SECRETS))


def test_startup_validation_rejects_missing_provider_approval(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "LIVE_SEND_VERIFICATION.md").write_text(
        yaml.safe_dump({
            "live_send_verification": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="docs/PROVIDER_APPROVAL.md is missing"):
        validate_config(copy.deepcopy(BASE_CONFIG), copy.deepcopy(BASE_SECRETS))


def test_startup_validation_rejects_outstanding_failures_in_lsv(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "PROVIDER_APPROVAL.md").write_text(
        yaml.safe_dump({
            "provider_approval": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    (docs_dir / "LIVE_SEND_VERIFICATION.md").write_text(
        yaml.safe_dump({
            "live_send_verification": {
                "operator_approval": {"approved": True},
                "outstanding_failures": ["429 rate limit unhandled"],
            }
        }),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="contains outstanding failures"):
        validate_config(copy.deepcopy(BASE_CONFIG), copy.deepcopy(BASE_SECRETS))


def test_startup_validation_rejects_missing_bot_token(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "PROVIDER_APPROVAL.md").write_text(
        yaml.safe_dump({
            "provider_approval": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    (docs_dir / "LIVE_SEND_VERIFICATION.md").write_text(
        yaml.safe_dump({
            "live_send_verification": {
                "operator_approval": {"approved": True},
                "outstanding_failures": [],
            }
        }),
        encoding="utf-8",
    )

    secrets_no_token = {"hmac_key": "some_secret_key_32_characters_min"}
    with pytest.raises(ConfigError, match="bot_token is required"):
        validate_config(copy.deepcopy(BASE_CONFIG), secrets_no_token)

