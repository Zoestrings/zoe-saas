"""Centralized Tool Registry for autonomous Zoe agents with typed schemas and execution sandboxing."""

import time
import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from zoe.agents.types import SecurityLevel, ToolDefinition
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.tools_registry")


class ToolExecutionError(Exception):
    pass


class ToolPermissionException(Exception):
    pass


class ToolRegistry:
    """Manages all registered tools available to autonomous agents."""

    _tools: Dict[str, ToolDefinition] = {}
    _handlers: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}

    @classmethod
    def register_tool(
        cls,
        definition: ToolDefinition,
        handler: Callable[..., Coroutine[Any, Any, Any]],
    ) -> None:
        """Register a tool with its schema definition and async handler."""
        cls._tools[definition.tool_id] = definition
        cls._handlers[definition.tool_id] = handler
        logger.debug("Registered agent tool: %s (%s)", definition.name, definition.tool_id)

    @classmethod
    def get_tool(cls, tool_id: str) -> Optional[ToolDefinition]:
        return cls._tools.get(tool_id)

    @classmethod
    def list_tools(cls) -> List[ToolDefinition]:
        return list(cls._tools.values())

    @classmethod
    def is_tool_authorized(cls, agent_id: str, tool_id: str) -> bool:
        """Check whether a tool is approved for a given agent."""
        from zoe.agents.specialized import SpecializedAgentRegistry
        cfg = SpecializedAgentRegistry.get_agent_config(agent_id)
        if not cfg:
            return False
        return tool_id in cfg.approved_tools

    @classmethod
    async def execute_tool(
        cls,
        tool_id: str,
        params: Dict[str, Any],
        agent_id: str = "general_agent",
        organization_id: str = "default_org",
    ) -> Dict[str, Any]:
        """Execute a registered tool within a bounded timeout and track metrics."""
        tool_def = cls.get_tool(tool_id)
        if not tool_def:
            raise ToolExecutionError(f"Tool '{tool_id}' not found in registry.")

        if not cls.is_tool_authorized(agent_id, tool_id):
            raise ToolPermissionException(f"Permission denied: Agent '{agent_id}' is not authorized to execute tool '{tool_id}'.")

        handler = cls._handlers.get(tool_id)
        if not handler:
            raise ToolExecutionError(f"No executable handler for tool '{tool_id}'.")

        start_time = time.time()
        try:
            # Execute with strict timeout
            result = await asyncio.wait_for(
                handler(params, organization_id=organization_id),
                timeout=float(tool_def.timeout_seconds),
            )
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "tool_id": tool_id,
                "data": result,
                "latency_ms": elapsed_ms,
                "cost_credits": tool_def.cost_credits,
            }
        except asyncio.TimeoutError:
            logger.error("Tool '%s' timed out after %ds", tool_id, tool_def.timeout_seconds)
            return {
                "success": False,
                "tool_id": tool_id,
                "error": f"Tool execution timed out after {tool_def.timeout_seconds} seconds.",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "cost_credits": 0,
            }
        except Exception as exc:
            logger.error("Error executing tool '%s': %s", tool_id, exc)
            return {
                "success": False,
                "tool_id": tool_id,
                "error": str(exc),
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "cost_credits": 0,
            }


# -------------------------------------------------------------
# Standard Tool Implementations Reusing Existing Zoe Infrastructure
# -------------------------------------------------------------

async def _tool_web_search(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.web_search import search_web
    query = params.get("query", "").strip()
    limit = int(params.get("limit", 6))
    if not query:
        return []
    return await search_web(query, limit=limit)


async def _tool_crypto_news(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.crypto_news import fetch_crypto_news
    topic = params.get("topic", "crypto").strip()
    limit = int(params.get("limit", 5))
    return await fetch_crypto_news(topic, max_results=limit)


async def _tool_scanner_security(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.scanner import scan_solana_token
    ca = params.get("contract_address", "").strip()
    if not ca:
        return {"valid": False, "error": "contract_address is required"}
    return await scan_solana_token(ca)


async def _tool_market_data(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.dexscreener import search_token_price_sync
    token = params.get("token", "").strip()
    if not token:
        return {"found": False}
    return search_token_price_sync(token)


async def _tool_x_sentiment(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.x_intel import analyze_x_sentiment
    target = params.get("target", "").strip()
    if not target:
        return {"sentiment": "neutral", "summary": "No target specified"}
    return await analyze_x_sentiment(target)


async def _tool_catalyst_events(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.tools.catalyst import get_upcoming_events
    query = params.get("query", "").strip()
    return await get_upcoming_events(query)


async def _tool_knowledge_rag(params: Dict[str, Any], organization_id: str) -> Any:
    from zoe.knowledge.retrieval import search
    project_id = params.get("project_id", organization_id)
    query = params.get("query", "").strip()
    try:
        chunks = search(project_id=project_id, query=query, top_k=3)
        return [
            {"source": getattr(c, "source_document", "doc"), "content": getattr(c, "chunk_text", str(c))}
            for c in chunks
        ]
    except Exception as exc:
        return [{"source": "system", "content": f"RAG search error: {str(exc)}"}]


async def _tool_generate_report(params: Dict[str, Any], organization_id: str) -> Any:
    title = params.get("title", "Zoe Intelligence Brief")
    summary = params.get("summary", "")
    sections = params.get("sections", [])
    sources = params.get("sources", [])
    
    lines = [f"# {title}\n", f"**Executive Summary:**\n{summary}\n"]
    for s in sections:
        lines.append(f"### {s.get('heading', 'Section')}\n{s.get('body', '')}\n")
    if sources:
        lines.append("### Verified Sources & Evidence")
        for src in sources:
            lines.append(f"- [{src.get('title', 'Source')}]({src.get('url', '#')}) ({src.get('domain', 'Web3')})")
    
    return {"report_markdown": "\n".join(lines)}


def initialize_default_tools() -> None:
    """Register the standard Zoe tool suite."""
    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="web_search",
            name="Live Web Search",
            description="Searches live web for current Web3 data and articles.",
            category="search",
            input_schema={"query": "string", "limit": "integer (optional)"},
            timeout_seconds=20,
            cost_credits=5,
        ),
        _tool_web_search,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="crypto_news",
            name="Web3 News Retrieval",
            description="Retrieves real-time crypto headlines and RSS stories with timestamps.",
            category="news",
            input_schema={"topic": "string", "limit": "integer (optional)"},
            timeout_seconds=15,
            cost_credits=5,
        ),
        _tool_crypto_news,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="scanner_security",
            name="Token Security Scanner",
            description="Runs deep on-chain audit (honeypot, mint/freeze authority, LP lock) on Solana and EVM.",
            category="security",
            input_schema={"contract_address": "string"},
            timeout_seconds=30,
            cost_credits=15,
        ),
        _tool_scanner_security,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="market_data",
            name="DexScreener Market Data",
            description="Fetches live token price, 24h volume, liquidity, FDV and pair addresses.",
            category="market",
            input_schema={"token": "string (symbol or CA)"},
            timeout_seconds=15,
            cost_credits=1,
        ),
        _tool_market_data,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="x_sentiment",
            name="X / CT Sentiment Analysis",
            description="Analyzes public sentiment and narratives on Crypto Twitter.",
            category="social",
            input_schema={"target": "string"},
            timeout_seconds=20,
            cost_credits=10,
        ),
        _tool_x_sentiment,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="catalyst_events",
            name="Upcoming Catalysts & Unlocks",
            description="Discovers token unlocks, conferences, hard forks, and roadmap milestones.",
            category="events",
            input_schema={"query": "string"},
            timeout_seconds=15,
            cost_credits=5,
        ),
        _tool_catalyst_events,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="knowledge_rag",
            name="Project Official Knowledge RAG",
            description="Searches verified official project whitepapers and technical documentation.",
            category="rag",
            input_schema={"query": "string", "project_id": "string (optional)"},
            timeout_seconds=10,
            cost_credits=1,
        ),
        _tool_knowledge_rag,
    )

    ToolRegistry.register_tool(
        ToolDefinition(
            tool_id="generate_report",
            name="Intelligence Report Formatter",
            description="Formats agent evidence, metrics, and citations into an audit-ready markdown report.",
            category="reports",
            input_schema={"title": "string", "summary": "string", "sections": "list", "sources": "list"},
            timeout_seconds=10,
            cost_credits=1,
        ),
        _tool_generate_report,
    )


# Automatically initialize on import
initialize_default_tools()
