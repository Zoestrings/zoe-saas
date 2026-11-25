"""Market Intelligence Agent specializing in pricing, liquidity, volume, and DEX analytics."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class MarketIntelligenceAgent(BaseAgent):
    """Fetches and interprets live liquidity, trading volume, price changes, and FDV."""

    def __init__(self):
        super().__init__(
            agent_id="market_agent",
            name="Market Intelligence Agent",
            description="Provides real-time token pricing, 24h volume, DEX liquidity, and market capitalization.",
            capabilities=["price_tracking", "liquidity_analysis", "volume_metrics", "fdv_calculation"],
            approved_tools=["market_data"],
            security_level=SecurityLevel.READ_ONLY,
            system_prompt="You are a Web3 Market Specialist. Interpret price action and market metrics factually.",
            timeout_seconds=20,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        token = request.payload.get("token") or request.payload.get("contract_address") or ""

        market_res = await self.execute_tool(
            "market_data",
            {"token": token},
            organization_id=request.organization_id,
        )
        tools_called.append("market_data")

        data = market_res.get("data", {}) if market_res.get("success") else {}
        found = data.get("found", False)

        return {
            "token": token,
            "market_data_found": found,
            "price_usd": data.get("price_usd"),
            "liquidity_usd": data.get("liquidity_usd"),
            "volume_24h_usd": data.get("volume_24h_usd"),
            "market_cap": data.get("market_cap"),
            "dex_url": data.get("pair_url"),
            "price_change_24h": data.get("price_change_24h"),
            "summary": f"Market data for {token}: Price ${data.get('price_usd', 'N/A')}, Liquidity ${data.get('liquidity_usd', 'N/A')}.",
        }, tools_called
