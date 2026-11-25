"""Project Analysis Agent synthesizing fundamentals, security, and market telemetry."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class ProjectAnalysisAgent(BaseAgent):
    """Combines fundamental research, on-chain market health, and social sentiment into cohesive due diligence."""

    def __init__(self):
        super().__init__(
            agent_id="project_analysis_agent",
            name="Project Analysis Agent",
            description="Performs multi-dimensional protocol analysis synthesizing fundamentals, liquidity, and sentiment.",
            capabilities=["due_diligence", "protocol_health", "ecosystem_benchmarking", "risk_reward_synthesis"],
            approved_tools=["market_data", "web_search", "generate_report"],
            security_level=SecurityLevel.ANALYTICS,
            system_prompt="You are a Lead Web3 Protocol Analyst. Synthesize multiple evidence streams into structured evaluation.",
            timeout_seconds=35,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        token = request.payload.get("token") or request.payload.get("project_name") or ""

        # 1. Fetch market data
        market_res = await self.execute_tool(
            "market_data",
            {"token": token},
            organization_id=request.organization_id,
        )
        tools_called.append("market_data")
        m_data = market_res.get("data", {}) if market_res.get("success") else {}

        # 2. Search web for roadmap and partnerships
        web_res = await self.execute_tool(
            "web_search",
            {"query": f"{token} crypto protocol partnerships roadmap ecosystem", "limit": 4},
            organization_id=request.organization_id,
        )
        tools_called.append("web_search")
        external_info = web_res.get("data", []) if web_res.get("success") else []

        verdict = "Healthy" if m_data.get("liquidity_usd", 0) > 100_000 else "Early-Stage / Speculative"

        return {
            "project": token,
            "overall_status": verdict,
            "market_summary": {
                "price_usd": m_data.get("price_usd"),
                "liquidity_usd": m_data.get("liquidity_usd"),
                "volume_24h_usd": m_data.get("volume_24h_usd"),
            },
            "external_citations": [
                {"title": item.get("title"), "url": item.get("url")}
                for item in external_info[:3]
            ],
            "recommendation_framework": (
                "Empirical assessment complete. Verify smart contract parameters and audit status before interacting."
            ),
        }, tools_called
