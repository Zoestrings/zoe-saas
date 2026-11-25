"""Security Analysis Agent performing on-chain contract audits, honeypot detection, and liquidity lock checks."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class SecurityAnalysisAgent(BaseAgent):
    """Executes on-chain security audits, rugpull checks, and holder concentration analysis."""

    def __init__(self):
        super().__init__(
            agent_id="security_agent",
            name="Security Analysis Agent",
            description="Performs deep on-chain audits, honeypot detection, mint/freeze verification, and LP lock analysis.",
            capabilities=["contract_audit", "honeypot_detection", "mint_freeze_check", "lp_lock_verification", "holder_concentration"],
            approved_tools=["scanner_security"],
            security_level=SecurityLevel.ANALYTICS,
            system_prompt="You are a Smart Contract Security Auditor. Highlight critical risk factors objectively.",
            timeout_seconds=35,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        ca = request.payload.get("contract_address") or request.payload.get("ca") or ""
        if not ca:
            return {
                "valid": False,
                "error": "contract_address is required for Security Analysis.",
            }, tools_called

        sec_res = await self.execute_tool(
            "scanner_security",
            {"contract_address": ca},
            organization_id=request.organization_id,
        )
        tools_called.append("scanner_security")

        report = sec_res.get("data", {}) if sec_res.get("success") else {}
        risk = report.get("risk", {})
        security = report.get("security", {})

        return {
            "valid": report.get("valid", False),
            "contract_address": ca,
            "chain": report.get("chain", "Solana"),
            "risk_level": risk.get("level", "UNKNOWN"),
            "risk_reasons": risk.get("reasons", []),
            "mint_revoked": security.get("mint_revoked"),
            "freeze_revoked": security.get("freeze_revoked"),
            "top_10_percent": security.get("top_10_holders_percent"),
            "lp_locked": security.get("lp_locked", True),
            "summary": f"Security audit for {ca}: Risk Level {risk.get('level', 'UNKNOWN')}.",
        }, tools_called
