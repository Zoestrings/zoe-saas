"""Agent Marketplace Foundation for discoverability, versioning, and capability cataloging."""

from typing import Any, Dict, List, Optional
from zoe.agents.specialized import SpecializedAgentRegistry


class AgentMarketplace:
    """Provides discoverability, ratings, categories, and capability profiles for agents."""

    @classmethod
    def get_catalog(cls) -> List[Dict[str, Any]]:
        """Return structured marketplace profiles for all specialized and custom agents."""
        agents = SpecializedAgentRegistry.list_agents()
        catalog = []

        categories_map = {
            "research_agent": "Due Diligence & Fundamentals",
            "news_agent": "Real-Time News & Events",
            "market_agent": "DEX & On-Chain Pricing",
            "narrative_agent": "Macro Trends & Narrative Sectors",
            "social_agent": "Sentiment & CT Intelligence",
            "project_analysis_agent": "Protocol Due Diligence",
            "security_agent": "Smart Contract Security",
            "dev_assistant_agent": "Developer Tooling",
            "community_mgmt_agent": "Community Operations",
            "verification_agent": "Fact-Checking & Quality Gates",
        }

        for ag in agents:
            cfg = ag.get_config()
            total = ag.total_invocations
            success = ag.successful_invocations
            # Compute empirical rating (4.0 to 5.0 base based on success rate)
            success_rate = (success / total) if total > 0 else 1.0
            rating = round(4.0 + (success_rate * 1.0), 1)

            catalog.append({
                "agent_id": cfg.agent_id,
                "name": cfg.name,
                "description": cfg.description,
                "category": categories_map.get(cfg.agent_id, "Intelligence"),
                "capabilities": cfg.capabilities,
                "approved_tools": cfg.approved_tools,
                "security_level": cfg.security_level.value,
                "version": "1.0.0",
                "is_active": cfg.is_active,
                "credit_cost": cfg.credit_cost_per_call,
                "credit_cost_per_call": cfg.credit_cost_per_call,
                "empirical_rating": rating,
                "total_runs": total,
                "success_rate_pct": round(success_rate * 100, 1),
            })

        return catalog

    @classmethod
    def get_marketplace_catalog(cls) -> Dict[str, Any]:
        """Return the complete categorized catalog of agents."""
        featured = cls.get_catalog()
        categories = list(set(a.get("category", "Intelligence") for a in featured))
        return {
            "categories": sorted(categories),
            "featured_agents": featured,
            "total_agents": len(featured),
        }
