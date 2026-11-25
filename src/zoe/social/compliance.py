"""Centralized X/Social Developer Policy Compliance & Feature Flag Gates.

All restricted X (Twitter) capabilities are disabled by default until explicit
platform authorization is configured via environment variables.
"""

import os
from typing import Dict


def is_x_api_enabled() -> bool:
    return os.getenv("X_API_ENABLED", "false").strip().lower() in ("1", "true", "yes")


def is_x_auto_reply_enabled() -> bool:
    return is_x_api_enabled() and os.getenv("X_AUTO_REPLY_ENABLED", "false").strip().lower() in ("1", "true", "yes")


def is_x_scraping_enabled() -> bool:
    return os.getenv("X_SCRAPING_ENABLED", "false").strip().lower() in ("1", "true", "yes")


def is_x_public_analytics_enabled() -> bool:
    return is_x_api_enabled() and os.getenv("X_PUBLIC_ANALYTICS_ENABLED", "false").strip().lower() in ("1", "true", "yes")


def get_social_compliance_status() -> Dict[str, object]:
    """Return non-secret compliance & feature-flag status for dashboards."""
    return {
        "x_api_enabled": is_x_api_enabled(),
        "x_auto_reply_enabled": is_x_auto_reply_enabled(),
        "x_scraping_enabled": is_x_scraping_enabled(),
        "x_public_analytics_enabled": is_x_public_analytics_enabled(),
        "permitted_channels": ["telegram_channel", "discord_webhook", "manual_export"],
        "policy_notice": (
            "X/Twitter automated publishing, replies, and scraping are disabled by default "
            "pending X Developer authorization. Research uses official docs, on-chain data, and news feeds."
        ),
    }


def assert_x_feature_enabled(feature: str) -> None:
    """Fail closed if a restricted X capability is invoked while disabled."""
    checks = {
        "x_api": is_x_api_enabled,
        "x_auto_reply": is_x_auto_reply_enabled,
        "x_scraping": is_x_scraping_enabled,
        "x_public_analytics": is_x_public_analytics_enabled,
    }
    fn = checks.get(feature)
    if fn is None or not fn():
        raise PermissionError(
            f"Restricted X capability '{feature}' is disabled by platform compliance policy."
        )
