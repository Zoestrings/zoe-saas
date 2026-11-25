"""Narrative Intelligence Agent tracking sector velocity, keyword clustering, and trend emergence."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class NarrativeIntelligenceAgent(BaseAgent):
    """Identifies and tracks emerging Web3 narrative sectors and attention shifts."""

    def __init__(self):
        super().__init__(
            agent_id="narrative_agent",
            name="Narrative Intelligence Agent",
            description="Analyzes macro Web3 trends, detects emerging narrative clusters, and tracks sector velocity.",
            capabilities=["narrative_clustering", "trend_detection", "keyword_tracking", "sector_velocity"],
            approved_tools=["crypto_news", "web_search"],
            security_level=SecurityLevel.READ_ONLY,
            system_prompt="You are a Web3 Narrative Analyst. Track and measure emerging sector trends factually.",
            timeout_seconds=25,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        topic = request.payload.get("topic") or request.payload.get("query") or "Web3 narrative trends"

        # Fetch recent news related to the narrative
        news_res = await self.execute_tool(
            "crypto_news",
            {"topic": topic, "limit": 6},
            organization_id=request.organization_id,
        )
        tools_called.append("crypto_news")

        articles = news_res.get("data", []) if news_res.get("success") else []

        from zoe.scanner.narratives import NarrativeDetectionEngine
        n_engine = NarrativeDetectionEngine()
        clusters = n_engine.extract_narratives_from_corpus(articles)

        return {
            "query": topic,
            "detected_clusters_count": len(clusters),
            "top_narrative": clusters[0].dict() if clusters else {},
            "all_clusters": [c.dict() for c in clusters[:4]],
            "articles_analyzed": len(articles),
            "summary": f"Detected {len(clusters)} narrative clusters for '{topic}'. Leading sector: {clusters[0].name if clusters else 'General'}.",
        }, tools_called
