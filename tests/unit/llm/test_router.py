import pytest
from unittest.mock import MagicMock
from zoe.llm.router import LLMRouter
from zoe.utils.errors import ProviderNotApprovedError


class DummyProvider:
    def __init__(self, name: str):
        self.name = name

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return f"{self.name} generated response"

    def classify(self, text: str, categories: list, **kwargs) -> str:
        return f"{self.name}_class"


def test_router_primary_success():
    primary = DummyProvider("mock_primary")
    fallback = DummyProvider("mock_fallback")
    router = LLMRouter(primary=primary, fallback=fallback)

    res = router.generate("system prompt", "user query")
    assert res == "mock_primary generated response"


def test_router_failover_on_primary_failure():
    primary = MagicMock()
    primary.name = "failing_primary"
    primary.generate.side_effect = RuntimeError("Primary API down")

    fallback = DummyProvider("healthy_fallback")
    router = LLMRouter(primary=primary, fallback=fallback)

    res = router.generate("system prompt", "user query")
    assert res == "healthy_fallback generated response"
    assert primary.generate.called


def test_router_both_fail_raises():
    primary = MagicMock()
    primary.name = "failing_primary"
    primary.generate.side_effect = RuntimeError("Primary down")

    fallback = MagicMock()
    fallback.name = "failing_fallback"
    fallback.generate.side_effect = RuntimeError("Fallback down")

    router = LLMRouter(primary=primary, fallback=fallback)

    with pytest.raises(RuntimeError, match="Fallback down"):
        router.generate("system prompt", "user query")


def test_router_sensitive_data_blocks_unapproved_primary():
    primary = MagicMock()
    primary.name = "unapproved_primary"
    fallback = DummyProvider("approved_fallback")

    # Only approved_fallback is in approved_providers
    router = LLMRouter(
        primary=primary,
        fallback=fallback,
        approved_providers={"approved_fallback"},
    )

    res = router.generate("system prompt", "sensitive user data", data_category="sensitive")
    assert res == "approved_fallback generated response"
    assert not primary.generate.called


def test_router_sensitive_data_no_approved_provider_raises():
    primary = DummyProvider("unapproved_primary")
    fallback = DummyProvider("unapproved_fallback")

    router = LLMRouter(
        primary=primary,
        fallback=fallback,
        approved_providers={"some_other_provider"},
    )

    with pytest.raises(ProviderNotApprovedError) as exc_info:
        router.generate("system prompt", "sensitive user data", data_category="sensitive")

    assert "No approved provider for sensitive data" in str(exc_info.value)


def test_router_classify_failover():
    primary = MagicMock()
    primary.name = "primary"
    primary.classify.side_effect = RuntimeError("Classify timeout")

    fallback = DummyProvider("fallback")
    router = LLMRouter(primary=primary, fallback=fallback)

    result = router.classify("Hello world", ["greeting", "question"])
    assert result == "fallback_class"

