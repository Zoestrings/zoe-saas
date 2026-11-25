"""Registry and exports of all foundational Zoe Specialized Agents."""

from typing import Dict, List, Type
from zoe.agents.base import BaseAgent
from zoe.agents.specialized.research import ResearchAgent
from zoe.agents.specialized.news import NewsIntelligenceAgent
from zoe.agents.specialized.market import MarketIntelligenceAgent
from zoe.agents.specialized.narrative import NarrativeIntelligenceAgent
from zoe.agents.specialized.social import SocialIntelligenceAgent
from zoe.agents.specialized.project_analysis import ProjectAnalysisAgent
from zoe.agents.specialized.security import SecurityAnalysisAgent
from zoe.agents.specialized.dev_assistant import DeveloperAssistanceAgent
from zoe.agents.specialized.community import CommunityManagementAgent
from zoe.agents.specialized.verification import VerificationAgent

STANDARD_AGENT_CLASSES: List[Type[BaseAgent]] = [
    ResearchAgent,
    NewsIntelligenceAgent,
    MarketIntelligenceAgent,
    NarrativeIntelligenceAgent,
    SocialIntelligenceAgent,
    ProjectAnalysisAgent,
    SecurityAnalysisAgent,
    DeveloperAssistanceAgent,
    CommunityManagementAgent,
    VerificationAgent,
]


class SpecializedAgentRegistry:
    """Manages instantiated specialized agents available for autonomous execution."""

    _agents: Dict[str, BaseAgent] = {}

    @classmethod
    def initialize(cls) -> None:
        """Instantiate all 10 standard agents."""
        for agent_cls in STANDARD_AGENT_CLASSES:
            agent_inst = agent_cls()
            cls._agents[agent_inst.agent_id] = agent_inst

    @classmethod
    def get_agent(cls, agent_id: str) -> BaseAgent:
        if not cls._agents:
            cls.initialize()
        agent = cls._agents.get(agent_id)
        if not agent:
            raise KeyError(f"Specialized agent '{agent_id}' not found.")
        return agent

    @classmethod
    def get_agent_config(cls, agent_id: str):
        if not cls._agents:
            cls.initialize()
        agent = cls._agents.get(agent_id)
        return agent.config if agent else None

    @classmethod
    def list_agents(cls) -> List[BaseAgent]:
        if not cls._agents:
            cls.initialize()
        return list(cls._agents.values())


# Initialize on import
SpecializedAgentRegistry.initialize()

__all__ = [
    "ResearchAgent",
    "NewsIntelligenceAgent",
    "MarketIntelligenceAgent",
    "NarrativeIntelligenceAgent",
    "SocialIntelligenceAgent",
    "ProjectAnalysisAgent",
    "SecurityAnalysisAgent",
    "DeveloperAssistanceAgent",
    "CommunityManagementAgent",
    "VerificationAgent",
    "SpecializedAgentRegistry",
]
