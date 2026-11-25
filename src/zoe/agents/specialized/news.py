"""News Intelligence Agent retrieving real-time headlines with source verification."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class NewsIntelligenceAgent(BaseAgent):
    """Monitors, filters, and summarizes real-time Web3 news and events."""

    def __init__(self):
        super().__init__(
            agent_id="news_agent",
            name="News Intelligence Agent",
            description="Tracks real-time Web3 breaking news, regulatory changes, and media developments.",
            capabilities=["breaking_news", "event_tracking", "source_attribution", "timestamp_validation"],
            approved_tools=["crypto_news", "catalyst_events"],
            security_level=SecurityLevel.READ_ONLY,
            system_prompt="You are a Web3 News Analyst. Report verified facts with source attribution.",
            timeout_seconds=25,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        topic = request.payload.get("topic") or request.payload.get("query") or "crypto"

        # 1. Fetch live news stories
        news_res = await self.execute_tool(
            "crypto_news",
            {"topic": topic, "limit": 5},
            organization_id=request.organization_id,
        )
        tools_called.append("crypto_news")

        articles = news_res.get("data", []) if news_res.get("success") else []

        # 2. Fetch upcoming catalysts
        catalyst_res = await self.execute_tool(
            "catalyst_events",
            {"query": topic},
            organization_id=request.organization_id,
        )
        tools_called.append("catalyst_events")
        catalysts = catalyst_res.get("data", []) if catalyst_res.get("success") else []

        return {
            "topic": topic,
            "articles_count": len(articles),
            "articles": articles,
            "upcoming_catalysts_count": len(catalysts),
            "catalysts": catalysts,
            "summary": f"Retrieved {len(articles)} verified news articles and {len(catalysts)} upcoming catalysts for {topic}.",
        }, tools_called
