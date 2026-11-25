"""LLM Router managing primary, fallback, and data sensitivity constraints."""

from typing import Any, List, Optional, Set
from zoe.llm.providers.protocol import LLMProvider
from zoe.utils.errors import ProviderNotApprovedError
from zoe.utils.logging import get_logger

logger = get_logger("zoe.llm.router")


class LLMRouter:
    """Routes requests between primary and fallback providers, enforcing sensitivity boundaries."""

    def __init__(
        self,
        primary: LLMProvider,
        fallback: Optional[LLMProvider] = None,
        approved_providers: Optional[Set[str]] = None,
    ):
        self.primary = primary
        self.fallback = fallback
        self.approved_providers: Set[str] = (
            set(approved_providers) if approved_providers is not None else {primary.name}
        )
        if fallback and approved_providers is None:
            self.approved_providers.add(fallback.name)

    def is_provider_approved_for_sensitive(self, provider_name: str) -> bool:
        return provider_name in self.approved_providers

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        data_category: str = "normal",
        **kwargs: Any,
    ) -> str:
        """Generate response adhering to data sensitivity and failover policies."""
        is_sensitive = data_category == "sensitive"

        primary_allowed = not is_sensitive or self.is_provider_approved_for_sensitive(self.primary.name)
        fallback_allowed = (
            self.fallback is not None
            and (not is_sensitive or self.is_provider_approved_for_sensitive(self.fallback.name))
        )

        if is_sensitive and not primary_allowed and not fallback_allowed:
            raise ProviderNotApprovedError(
                f"No approved provider for sensitive data. Configured providers: "
                f"primary='{self.primary.name}', fallback='{self.fallback.name if self.fallback else None}'. "
                f"Approved providers: {self.approved_providers}"
            )

        # Attempt primary if allowed
        if primary_allowed:
            try:
                result = self.primary.generate(system_prompt, user_prompt, **kwargs)
                self._record_llm_usage(self.primary, system_prompt, user_prompt, result)
                return result
            except Exception as e:
                logger.warning(
                    "Primary provider '%s' failed: %s", self.primary.name, str(e)
                )
                if not fallback_allowed:
                    if is_sensitive and self.fallback and not self.is_provider_approved_for_sensitive(self.fallback.name):
                        raise ProviderNotApprovedError(
                            f"Fallback provider '{self.fallback.name}' is not approved for sensitive data."
                        ) from e
                    raise

        # Attempt fallback
        if fallback_allowed and self.fallback is not None:
            logger.info("Failing over to fallback provider '%s'", self.fallback.name)
            try:
                result = self.fallback.generate(system_prompt, user_prompt, **kwargs)
                self._record_llm_usage(self.fallback, system_prompt, user_prompt, result)
                return result
            except Exception as e:
                logger.error("Fallback provider '%s' also failed: %s", self.fallback.name, str(e))
                raise

        raise ProviderNotApprovedError(
            f"Provider '{self.primary.name}' is not approved for sensitive data."
        )

    @staticmethod
    def _record_llm_usage(provider: LLMProvider, system_prompt: str, user_prompt: str, response_text: str) -> None:
        """Record prompt/completion tokens, model name, and estimated USD cost into `llm_usage`."""
        import os
        from pathlib import Path
        import sqlite3
        from datetime import datetime, timezone

        try:
            usage = getattr(provider, "last_usage", None) or {}
            prompt_tokens = int(usage.get("prompt_tokens") or max(1, (len(system_prompt) + len(user_prompt)) // 4))
            completion_tokens = int(usage.get("completion_tokens") or max(1, len(response_text or "") // 4))
            model_name = str(getattr(provider, "model", getattr(provider, "name", "unknown")))
            provider_name = str(getattr(provider, "name", "unknown"))

            # Conservative cost estimation ($0.20 / 1M input, $0.60 / 1M output)
            est_cost_usd = round((prompt_tokens * 0.0000002) + (completion_tokens * 0.0000006), 8)

            data_dir = Path(os.getenv("DATA_DIR", "data"))
            op_db = data_dir / "operational" / "operational.db"
            if not op_db.parent.exists():
                return
            conn = sqlite3.connect(str(op_db), timeout=5.0)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO llm_usage (provider, model, prompt_tokens, completion_tokens, estimated_cost_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider_name, model_name, prompt_tokens, completion_tokens, est_cost_usd, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.debug("Non-fatal error recording llm_usage: %s", exc)

    def classify(
        self,
        text: str,
        categories: List[str],
        data_category: str = "normal",
        **kwargs: Any,
    ) -> str:
        """Classify message with failover support."""
        try:
            return self.primary.classify(text, categories, **kwargs)
        except Exception as e:
            if self.fallback:
                logger.warning("Primary classify failed (%s), trying fallback: %s", self.primary.name, str(e))
                return self.fallback.classify(text, categories, **kwargs)
            raise

