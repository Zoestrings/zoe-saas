"""Research Agent specializing in deep project due diligence and official documentation."""

from typing import Any, Dict, List, Tuple
from zoe.agents.base import BaseAgent
from zoe.agents.types import AgentTaskRequest, SecurityLevel


class ResearchAgent(BaseAgent):
    """Conducts deep-dive fundamental research on Web3 protocols and tokens."""

    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            description="Performs fundamental analysis, whitepaper review, and project background research.",
            capabilities=["whitepaper_analysis", "roadmap_evaluation", "team_verification", "docs_retrieval"],
            approved_tools=["knowledge_rag", "web_search"],
            security_level=SecurityLevel.READ_ONLY,
            system_prompt="You are a Web3 Research Specialist focusing on fundamental value and architecture.",
            timeout_seconds=30,
        )

    async def _process_task(self, request: AgentTaskRequest) -> Tuple[Dict[str, Any], List[str]]:
        tools_called = []
        query = request.payload.get("query", "")
        project_id = request.payload.get("project_id", request.project_id or "")

        findings = []
        # 1. Search official knowledge base (RAG)
        rag_res = await self.execute_tool(
            "knowledge_rag",
            {"query": query, "project_id": project_id},
            organization_id=request.organization_id,
        )
        tools_called.append("knowledge_rag")
        if rag_res.get("success"):
            findings.extend(rag_res.get("data", []))

        # 2. Search web for external project documentation
        web_res = await self.execute_tool(
            "web_search",
            {"query": f"{query} crypto documentation whitepaper overview", "limit": 4},
            organization_id=request.organization_id,
        )
        tools_called.append("web_search")

        external_sources = []
        if web_res.get("success"):
            for item in web_res.get("data", []):
                external_sources.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("snippet"),
                })

        return {
            "query": query,
            "project_id": project_id,
            "official_docs_found": len(findings),
            "official_chunks": findings,
            "external_sources": external_sources,
            "summary": f"Research completed for '{query}'. Found {len(findings)} official doc chunks and {len(external_sources)} external sources.",
        }, tools_called
