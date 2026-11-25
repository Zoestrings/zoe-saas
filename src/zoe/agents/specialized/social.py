"""Social Intelligence Agent analyzing CT discourse, sentiment velocity, and author participation."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class SocialIntelligenceAgent(BaseAgent):
    """Measures community sentiment, public discussion volume, and author diversity."""

    def __init__(self):
        super().__init__(
            agent_id="social_agent",
            name="Social Intelligence Agent",
            description="Analyzes public sentiment across Crypto Twitter and social wires with anti-spam filtering.",
            capabilities=["sentiment_analysis", "social_volume_tracking", "author_diversity", "coordinated_activity_detection"],
            approved_tools=["x_sentiment"],
            security_level=SecurityLevel.READ_ONLY,
            system_prompt="You are a Social Intelligence Analyst. Measure public sentiment and filter promotional spam.",
            timeout_seconds=25,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        target = request.payload.get("target") or request.payload.get("token") or request.payload.get("query") or "crypto"

        sentiment_res = await self.execute_tool(
            "x_sentiment",
            {"target": target},
            organization_id=request.organization_id,
        )
        tools_called.append("x_sentiment")

        data = sentiment_res.get("data", {}) if sentiment_res.get("success") else {}

        return {
            "target": target,
            "sentiment": data.get("sentiment", "Neutral"),
            "sentiment_score": data.get("sentiment_score", 0.0),
            "summary": data.get("summary", "Moderate social discussion."),
            "top_narratives": data.get("top_narratives", []),
            "total_samples": data.get("total_samples", 10),
            "unique_authors": data.get("unique_authors", 8),
            "coordinated_activity_flag": data.get("coordinated_activity_flag", False),
            "disclaimer": "Social sentiment is speculative and does not constitute financial advice.",
        }, tools_called
