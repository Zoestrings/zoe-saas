import os
from pathlib import Path
from typing import Any, Dict
import yaml

from zoe.utils.errors import ConfigError

ALLOWED_TOP_LEVEL = {
    "project",
    "telegram",
    "personality",
    "participation",
    "knowledge",
    "memory",
    "safety",
    "escalation",
    "token_address",
    "modules",
    "display_name",
    "links",
}

ALLOWED_NESTED = {
    "links": {
        "website",
        "twitter",
        "telegram",
        "tiktok",
    },
    "modules": {
        "community_manager",
        "crypto_intelligence",
        "community_intelligence",
        "wallet_intelligence",
        "alerts_monitoring",
        "caller_reputation",
    },
    "project": {
        "id", "name", "description", "version", "created_at", "active", "token_address", "display_name",
    },
    "telegram": {
        "environment", "group_id", "live_poll_enabled", "live_send_approved",
        "live_send_responses_enabled", "live_send_moderator_notifications_enabled",
        "poll_timeout_seconds", "poll_interval_seconds", "bot_username",
        "moderator_channel_id", "live_send_enabled",
    },
    "personality": {
        "name", "system_prompt", "tone", "language", "guidelines", "style", "display_name",
    },
    "participation": {
        "mode", "cooldown_seconds", "rate_limit_seconds", "max_daily_messages",
        "rate_limit_per_minute", "silence_reasons", "allowed_topics", "ignored_topics",
        "respond_to_casual"
    },
    "knowledge": {
        "db_path", "index_path", "chunk_size", "chunk_overlap",
        "embedding_model", "top_k", "similarity_threshold"
    },
    "memory": {
        "db_path", "short_term_window", "long_term_retention_days",
        "summary_interval_hours"
    },
    "safety": {
        "enabled", "content_filter", "max_token_length", "banned_words",
        "pii_detection", "block_patterns", "url_allowlist"
    },
    "escalation": {
        "acknowledgement_deadline_minutes", "channels", "admin_user_ids",
        "moderator_group_id", "critical_alert_threshold"
    },
}

SECRET_KEY_NAMES = {
    "bot_token",
    "hmac_key",
    "provider_api_key",
    "api_key",
    "secret",
    "secret_key",
    "password",
    "private_key",
    "webhook_secret",
    "auth_token",
}

VALID_TELEGRAM_ENVIRONMENTS = {"live_verification", "pilot", "production"}


def _get_project_root() -> Path:
    # src/zoe/settings.py -> root is 3 levels up
    return Path(__file__).resolve().parent.parent.parent


def _check_no_secrets(data: Any, path: str = "") -> None:
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else str(k)
            key_lower = str(k).lower()
            if key_lower in SECRET_KEY_NAMES or any(s in key_lower for s in ("bot_token", "hmac_key", "provider_api_key")):
                raise ConfigError(f"Secret-like key '{current_path}' is not permitted in public config.")
            _check_no_secrets(v, current_path)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            _check_no_secrets(item, f"{path}[{idx}]")


def _validate_structure(config: Dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ConfigError("Config must be a dictionary.")

    for top_k in config.keys():
        if top_k not in ALLOWED_TOP_LEVEL:
            raise ConfigError(f"Unknown top-level field '{top_k}' in config.")

        section = config[top_k]
        if isinstance(section, dict) and top_k in ALLOWED_NESTED:
            allowed = ALLOWED_NESTED[top_k]
            for nested_k in section.keys():
                if nested_k not in allowed:
                    raise ConfigError(f"Unknown field '{nested_k}' under section '{top_k}'.")


def validate_config(config: Dict[str, Any], secrets: Dict[str, Any]) -> None:
    """Validate project configuration and secrets rules."""
    _check_no_secrets(config)
    _validate_structure(config)

    telegram_cfg = config.get("telegram", {})
    if not isinstance(telegram_cfg, dict):
        raise ConfigError("telegram section must be a dictionary.")

    # Reject legacy live_send_enabled flag
    if "live_send_enabled" in telegram_cfg:
        raise ConfigError("Legacy flag 'telegram.live_send_enabled' has been removed and is not permitted.")

    live_poll = telegram_cfg.get("live_poll_enabled", False)
    live_send = telegram_cfg.get("live_send_approved", False)
    live_resp = telegram_cfg.get("live_send_responses_enabled", False)
    live_mod = telegram_cfg.get("live_send_moderator_notifications_enabled", False)
    any_live_enabled = live_poll or live_send or live_resp or live_mod

    # Validate telegram.environment if any live flag is true
    if any_live_enabled:
        env = telegram_cfg.get("environment")
        if env not in VALID_TELEGRAM_ENVIRONMENTS:
            raise ConfigError(
                f"telegram.environment must be one of {sorted(VALID_TELEGRAM_ENVIRONMENTS)} when live flags are enabled; got '{env}'."
            )

    # Stage 8 Live Send Gate validation:
    if any_live_enabled:
        root = _get_project_root()
        # Prefer cwd/docs if it exists (e.g. in isolated test environments)
        pa_path = Path("docs") / "PROVIDER_APPROVAL.md" if Path("docs").exists() else root / "docs" / "PROVIDER_APPROVAL.md"
        lsv_path = Path("docs") / "LIVE_SEND_VERIFICATION.md" if Path("docs").exists() else root / "docs" / "LIVE_SEND_VERIFICATION.md"

        # Check PROVIDER_APPROVAL.md
        if not pa_path.exists():
            raise ConfigError("docs/PROVIDER_APPROVAL.md is missing but live send is enabled.")
        try:
            with open(pa_path, "r", encoding="utf-8") as f:
                pa_data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"docs/PROVIDER_APPROVAL.md could not be parsed: {e}")

        if not isinstance(pa_data, dict) or "provider_approval" not in pa_data:
            raise ConfigError("docs/PROVIDER_APPROVAL.md missing 'provider_approval' section.")
        pa = pa_data["provider_approval"]
        if not pa.get("operator_approval", {}).get("approved"):
            raise ConfigError("docs/PROVIDER_APPROVAL.md is not approved by operator.")
        if pa.get("outstanding_failures"):
            raise ConfigError("docs/PROVIDER_APPROVAL.md contains outstanding failures.")

        # Check LIVE_SEND_VERIFICATION.md
        if not lsv_path.exists():
            raise ConfigError("docs/LIVE_SEND_VERIFICATION.md is missing but live send is enabled.")
        try:
            with open(lsv_path, "r", encoding="utf-8") as f:
                lsv_data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"docs/LIVE_SEND_VERIFICATION.md could not be parsed: {e}")

        if not isinstance(lsv_data, dict) or "live_send_verification" not in lsv_data:
            raise ConfigError("docs/LIVE_SEND_VERIFICATION.md missing 'live_send_verification' section.")
        lsv = lsv_data["live_send_verification"]
        if not lsv.get("operator_approval", {}).get("approved"):
            raise ConfigError("docs/LIVE_SEND_VERIFICATION.md is not approved by operator.")
        if lsv.get("outstanding_failures"):
            raise ConfigError("docs/LIVE_SEND_VERIFICATION.md contains outstanding failures.")

        # Check secrets
        if not secrets or not secrets.get("bot_token"):
            raise ConfigError("bot_token is required in project secrets when live flags are enabled.")


def load_project_config(project_id: str) -> Dict[str, Any]:
    """Load and validate public project config from config/projects/{project_id}.yaml."""
    clean_id = project_id[:-5] if project_id.endswith(".yaml") else project_id
    filename = f"{clean_id}.yaml"

    paths_to_try = [
        Path("config") / "projects" / filename,
        _get_project_root() / "config" / "projects" / filename,
    ]

    config_path = None
    for p in paths_to_try:
        if p.exists():
            config_path = p
            break

    if config_path is None:
        raise ConfigError(f"Config file not found for project '{project_id}': looked in {paths_to_try}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ConfigError(f"Config file for '{project_id}' is empty.")

    _check_no_secrets(data)
    _validate_structure(data)

    return data


def load_project_secrets(project_id: str) -> Dict[str, Any]:
    """Load project secrets from config/secrets/{project_id}.secrets.yaml or environment variables."""
    clean_id = project_id[:-5] if project_id.endswith(".yaml") else project_id
    filename = f"{clean_id}.secrets.yaml"

    paths_to_try = [
        Path("config") / "secrets" / filename,
        _get_project_root() / "config" / "secrets" / filename,
    ]

    data = {}
    for p in paths_to_try:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded is not None:
                    data.update(loaded)
            break

    # Environment variable fallbacks for production cloud deployments (Railway/Docker)
    import os
    env_token_key = f"{clean_id.upper()}_BOT_TOKEN"
    bot_token = os.getenv(env_token_key) or os.getenv("TELEGRAM_BOT_TOKEN")
    if bot_token and not data.get("bot_token"):
        data["bot_token"] = bot_token

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and not data.get("groq_api_key"):
        data["groq_api_key"] = groq_key

    if not data.get("hmac_key"):
        data["hmac_key"] = os.getenv(f"{clean_id.upper()}_HMAC_KEY", f"zoe_{clean_id}_hmac_secret_key_32_characters_minimum")

    return data

