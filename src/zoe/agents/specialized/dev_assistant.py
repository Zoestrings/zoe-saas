"""Developer Assistance Agent providing smart contract architecture reviews and technical guidance."""

import re
from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class DeveloperAssistanceAgent(BaseAgent):
    """Provides technical smart contract architectural reviews, security heuristics, and tooling advice."""

    def __init__(self):
        super().__init__(
            agent_id="dev_assistant_agent",
            name="Developer Assistance Agent",
            description="Assists Web3 developers with contract architecture reviews, vulnerability heuristics, and SDK integration.",
            capabilities=["contract_review", "vulnerability_heuristics", "gas_optimization", "sdk_guidance"],
            approved_tools=["knowledge_rag", "web_search"],
            security_level=SecurityLevel.ANALYTICS,
            system_prompt="You are a Senior Smart Contract Architect. Focus on security, safety checks, and best practices.",
            timeout_seconds=30,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        code_or_query = request.payload.get("code") or request.payload.get("query") or ""

        # Check for known vulnerability patterns
        vulnerabilities_detected = []
        if re.search(r"\b(?:tx\.origin|selfdestruct|call\.value)\b", code_or_query, re.IGNORECASE):
            vulnerabilities_detected.append("Usage of risky EVM opcodes (tx.origin, selfdestruct, or raw call.value).")

        if re.search(r"\b(?:unchecked_math|reentrancy)\b", code_or_query, re.IGNORECASE):
            vulnerabilities_detected.append("Potential reentrancy vulnerability or unchecked arithmetic.")

        # Search documentation for best practices
        rag_res = await self.execute_tool(
            "knowledge_rag",
            {"query": "smart contract security best practices reentrancy", "project_id": request.project_id or ""},
            organization_id=request.organization_id,
        )
        tools_called.append("knowledge_rag")

        return {
            "query": code_or_query[:200],
            "vulnerability_flags": vulnerabilities_detected,
            "security_advice": (
                "Ensure Checks-Effects-Interactions pattern is strictly followed. Use OpenZeppelin audited libraries for token contracts."
            ),
            "findings_count": len(vulnerabilities_detected),
            "status": "PASS" if not vulnerabilities_detected else "REVIEW_REQUIRED",
        }, tools_called
