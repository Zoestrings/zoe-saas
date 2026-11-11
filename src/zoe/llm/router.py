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
                return self.primary.generate(system_prompt, user_prompt, **kwargs)
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
                return self.fallback.generate(system_prompt, user_prompt, **kwargs)
            except Exception as e:
                logger.error("Fallback provider '%s' also failed: %s", self.fallback.name, str(e))
                raise

        raise ProviderNotApprovedError(
            f"Provider '{self.primary.name}' is not approved for sensitive data."
        )

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

