"""Security policies, guardrails, and sandboxing for autonomous agents."""

import re
from typing import Any, Dict, List, Optional, Tuple
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.security")

# Strictly forbidden capabilities and keywords
BLOCKED_PATTERNS = [
    re.compile(r"\b(?:seed\s+phrase|private\s+key|secret\s+key|wallet\s+mnemonic)\b", re.IGNORECASE),
    re.compile(r"\b(?:transfer\s+(?:all\s+)?(?:funds|tokens|sol|eth|usdt)|drain\s+wallet|send\s+(?:\d+(?:\.\d+)?\s+)?(?:sol|eth|usdt)\s+to)\b", re.IGNORECASE),
    re.compile(r"\b(?:exec\s*\(|eval\s*\(|subprocess|os\.system|shell\s+exec)\b", re.IGNORECASE),
    re.compile(r"\b(?:ignore\s+all\s+previous\s+instructions|system\s+prompt\s+override)\b", re.IGNORECASE),
]


class AgentSecurityException(Exception):
    """Raised when an agent violates security or privacy policies."""
    pass


class AgentSecurityPolicy:
    """Enforces non-negotiable platform safety and tenant isolation rules."""

    MAX_TASK_STEPS: int = 12
    MAX_EXECUTION_TIME_SECONDS: int = 90
    ALLOW_WALLET_SIGNING_DEFAULT: bool = False

    @staticmethod
    def validate_task_request(
        action: str,
        payload: Dict[str, Any],
        organization_id: str,
        allowed_tools: List[str],
        requested_tool: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validate an inbound task request against security constraints."""
        # 1. Organization boundary check
        if not organization_id or organization_id.strip() == "":
            return False, "Security violation: organization_id is required for multi-tenant isolation."

        # 2. Tool permission authorization check
        if requested_tool:
            if requested_tool not in allowed_tools:
                return False, f"Access denied: tool '{requested_tool}' is not in the agent's approved tools."

        # 3. Payload inspection for dangerous directives
        payload_str = str(payload).lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.search(payload_str):
                logger.critical(
                    "Security alert: Malicious or restricted pattern detected in agent payload: %s",
                    pattern.pattern,
                )
                return False, "Security policy violation: Request contains restricted or forbidden directives."

        # 4. Action validation (prevent dunder or code injection)
        if action.startswith("__") or re.search(r"\b(?:eval|exec)\b", action):
            return False, f"Invalid action format: '{action}'."

        return True, None

    @staticmethod
    def sanitize_untrusted_content(text: str) -> str:
        """Strip potential prompt-injection tags or control characters from external text."""
        if not text:
            return ""
        # Remove XML/HTML style system tags
        sanitized = re.sub(r"<\s*/?(?:system|assistant|user|instructions)[^>]*>", "", text, flags=re.IGNORECASE)
        # Remove markdown link hijacking or javascript protocol
        sanitized = re.sub(r"javascript\s*:", "", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    @staticmethod
    def assert_organization_isolation(
        current_org: str,
        target_org: str,
        resource_name: str = "resource",
    ) -> None:
        """Ensure an agent execution cannot access data belonging to another tenant."""
        if current_org != "global" and target_org != "global" and current_org != target_org:
            raise AgentSecurityException(
                f"Multi-tenant breach prevented: Cannot access {resource_name} of org '{target_org}' from org '{current_org}'."
            )
