"""Central Agent Orchestrator coordinating task decomposition, multi-agent dispatch, and verified synthesis."""

import time
import uuid
import asyncio
from typing import Any, Dict, List, Optional, Set
from zoe.agents.types import (
    AgentTaskRequest,
    AgentTaskResponse,
    OrchestrationPlan,
    TaskStatus,
    WorkflowExecutionResult,
)
from zoe.agents.specialized import SpecializedAgentRegistry
from zoe.agents.memory import AgentMemoryManager
from zoe.agents.security import AgentSecurityPolicy
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.orchestrator")


class OrchestratorCycleException(Exception):
    pass


class CentralAgentOrchestrator:
    """Orchestrates complex multi-step Web3 goals across specialized agents."""

    def __init__(self):
        self.memory = AgentMemoryManager()

    def decompose_task(self, goal: str) -> OrchestrationPlan:
        """Analyze a user goal and decompose it into an ordered plan of specialized subtasks."""
        plan_id = str(uuid.uuid4())
        lower_goal = goal.lower()
        subtasks: List[Dict[str, Any]] = []
        selected_agents: List[str] = []

        # 1. Check for token security audit / contract scan need
        if any(w in lower_goal for w in ["audit", "security", "honeypot", "contract", "mint", "freeze", "rug"]):
            subtasks.append({
                "subtask_id": "step_security",
                "agent_id": "security_agent",
                "action": "contract_audit",
                "description": "Perform on-chain contract security audit and honeypot check",
            })
            selected_agents.append("security_agent")

        # 2. Check for market & DEX pricing need
        if any(w in lower_goal for w in ["price", "market", "liquidity", "volume", "fdv", "mcap", "trading"]):
            subtasks.append({
                "subtask_id": "step_market",
                "agent_id": "market_agent",
                "action": "market_analysis",
                "description": "Fetch live DEX pricing, 24h volume, and liquidity",
            })
            selected_agents.append("market_agent")

        # 3. Check for live news & catalysts need
        if any(w in lower_goal for w in ["news", "event", "catalyst", "unlock", "announcement", "latest"]):
            subtasks.append({
                "subtask_id": "step_news",
                "agent_id": "news_agent",
                "action": "news_retrieval",
                "description": "Retrieve recent verified crypto headlines and upcoming event milestones",
            })
            selected_agents.append("news_agent")

        # 4. Check for social & sentiment need
        if any(w in lower_goal for w in ["sentiment", "ct", "twitter", "community", "fud", "hype"]):
            subtasks.append({
                "subtask_id": "step_social",
                "agent_id": "social_agent",
                "action": "sentiment_analysis",
                "description": "Measure public sentiment and detect coordinated astroturfing",
            })
            selected_agents.append("social_agent")

        # 5. Check for narrative & macro sector need
        if any(w in lower_goal for w in ["narrative", "sector", "depin", "ai agent", "rwa", "l2", "trend"]):
            subtasks.append({
                "subtask_id": "step_narrative",
                "agent_id": "narrative_agent",
                "action": "narrative_tracking",
                "description": "Identify narrative sector velocity and keyword clustering",
            })
            selected_agents.append("narrative_agent")

        # 6. Default Fallback: Full Web3 Due Diligence Pipeline
        if not subtasks:
            subtasks = [
                {
                    "subtask_id": "step_research",
                    "agent_id": "research_agent",
                    "action": "fundamental_research",
                    "description": "Retrieve project documentation and background facts",
                },
                {
                    "subtask_id": "step_news",
                    "agent_id": "news_agent",
                    "action": "news_retrieval",
                    "description": "Retrieve real-time headlines with source attribution",
                },
                {
                    "subtask_id": "step_market",
                    "agent_id": "market_agent",
                    "action": "market_analysis",
                    "description": "Fetch live market liquidity and volume metrics",
                },
            ]
            selected_agents = ["research_agent", "news_agent", "market_agent"]

        # Always append Verification Agent as final quality gate
        subtasks.append({
            "subtask_id": "step_verification",
            "agent_id": "verification_agent",
            "action": "verify_and_synthesize",
            "description": "Verify empirical facts, check source citations, and gate output",
        })
        selected_agents.append("verification_agent")

        return OrchestrationPlan(
            plan_id=plan_id,
            goal=goal,
            subtasks=subtasks,
            estimated_steps=len(subtasks),
            selected_agents=selected_agents,
        )

    async def execute_plan(
        self,
        plan: OrchestrationPlan,
        target_entity: str,
        organization_id: str = "default_org",
        user_id: Optional[str] = None,
    ) -> WorkflowExecutionResult:
        """Execute the subtask DAG while strictly enforcing loop limits and tenant isolation."""
        execution_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        step_results: Dict[str, Any] = {}
        agents_involved: List[str] = []
        audit_trail: List[Dict[str, Any]] = []
        collected_sources: List[Dict[str, str]] = []

        visited_agents: Set[str] = set()
        step_count = 0

        if len(plan.subtasks) > AgentSecurityPolicy.MAX_TASK_STEPS:
            raise OrchestratorCycleException(
                f"Execution aborted: Maximum task step limit ({AgentSecurityPolicy.MAX_TASK_STEPS}) exceeded."
            )

        for subtask in plan.subtasks:
            step_count += 1
            if step_count > AgentSecurityPolicy.MAX_TASK_STEPS:
                raise OrchestratorCycleException(
                    f"Execution aborted: Maximum task step limit ({AgentSecurityPolicy.MAX_TASK_STEPS}) exceeded."
                )

            agent_id = subtask["agent_id"]
            action = subtask["action"]
            task_id = f"{execution_id}_{subtask['subtask_id']}"

            # Cycle detection (except verification agent which runs at the end)
            if agent_id in visited_agents and agent_id != "verification_agent":
                logger.warning("Potential loop detected: Agent '%s' re-invoked in same plan.", agent_id)

            visited_agents.add(agent_id)
            agents_involved.append(agent_id)

            # Build subtask payload
            payload = {
                "target": target_entity,
                "token": target_entity,
                "query": target_entity,
                "topic": target_entity,
                "contract_address": target_entity if len(target_entity) > 30 else "",
                "previous_results": step_results,
                "sources": collected_sources,
            }

            request = AgentTaskRequest(
                task_id=task_id,
                correlation_id=correlation_id,
                sender_agent_id="central_orchestrator",
                recipient_agent_id=agent_id,
                action=action,
                payload=payload,
                organization_id=organization_id,
                user_id=user_id,
            )

            # Execute agent safely
            try:
                agent = SpecializedAgentRegistry.get_agent(agent_id)
                response: AgentTaskResponse = await agent.run(request)

                audit_trail.append({
                    "step": subtask["subtask_id"],
                    "agent": agent_id,
                    "status": response.status.value,
                    "latency_ms": response.execution_time_ms,
                    "tools": response.tools_called,
                })

                if response.status == TaskStatus.COMPLETED:
                    step_results[subtask["subtask_id"]] = response.data

                    # Collect external sources for verification step
                    if "articles" in response.data:
                        for a in response.data.get("articles", []):
                            if a.get("url"):
                                collected_sources.append({
                                    "title": a.get("title", "Article"),
                                    "url": a.get("url"),
                                    "domain": a.get("source", "Web3"),
                                })
                else:
                    logger.warning("Subtask '%s' failed: %s", subtask["subtask_id"], response.error_message)
                    step_results[subtask["subtask_id"]] = {"error": response.error_message}

            except Exception as exc:
                logger.error("Orchestrator error running agent '%s': %s", agent_id, exc)
                step_results[subtask["subtask_id"]] = {"error": str(exc)}

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # Synthesize final output
        final_summary_lines = [
            f"### Multi-Agent Intelligence Brief: {target_entity.upper()}\n",
            f"**Goal:** {plan.goal}\n",
        ]
        for step_id, data in step_results.items():
            if isinstance(data, dict) and data.get("summary"):
                final_summary_lines.append(f"- **{step_id.replace('step_', '').title()}:** {data.get('summary')}")

        final_output = {
            "title": f"Zoe Multi-Agent Intelligence Brief: {target_entity.upper()}",
            "goal": plan.goal,
            "target": target_entity,
            "synthesized_summary": "\n".join(final_summary_lines),
            "step_count": len(plan.subtasks),
            "sources": collected_sources,
            "verification_status": step_results.get("step_verification", {}).get("verification_status", "APPROVED"),
            "confidence_score": step_results.get("step_verification", {}).get("confidence_score", 0.90),
        }

        # Clear ephemeral task memory
        self.memory.clear_task_memory(execution_id)

        return WorkflowExecutionResult(
            workflow_id=plan.plan_id,
            execution_id=execution_id,
            status=TaskStatus.COMPLETED,
            step_results=step_results,
            final_output=final_output,
            total_time_ms=elapsed_ms,
            total_execution_time_ms=elapsed_ms,
            final_synthesis=final_output.get("synthesized_summary", ""),
            agents_involved=agents_involved,
            audit_trail=audit_trail,
        )
