"""Autonomous Workflow Engine managing multi-agent pipelines with step dependencies and audit trails."""

import time
import uuid
from typing import Any, Dict, List, Optional
from zoe.agents.types import (
    AgentTaskRequest,
    AgentTaskResponse,
    TaskStatus,
    WorkflowDefinition,
    WorkflowExecutionResult,
    WorkflowStep,
)
from zoe.agents.specialized import SpecializedAgentRegistry
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.workflows")

# Pre-configured Standard Autonomous Workflows
STANDARD_WORKFLOWS: Dict[str, WorkflowDefinition] = {
    "project_due_diligence": WorkflowDefinition(
        workflow_id="project_due_diligence",
        name="Full Web3 Project Due Diligence",
        description="Coordinates Research, News, Market, Security, and Verification agents for complete protocol evaluation.",
        steps=[
            WorkflowStep(step_id="w1_research", name="Fundamental Research", agent_id="research_agent", action="fundamental_research"),
            WorkflowStep(step_id="w1_news", name="News Intelligence", agent_id="news_agent", action="news_retrieval", depends_on=["w1_research"]),
            WorkflowStep(step_id="w1_market", name="DEX Market Analytics", agent_id="market_agent", action="market_analysis", depends_on=["w1_research"]),
            WorkflowStep(step_id="w1_security", name="On-Chain Security Audit", agent_id="security_agent", action="contract_audit", depends_on=["w1_market"]),
            WorkflowStep(step_id="w1_verify", name="Fact-Checking Quality Gate", agent_id="verification_agent", action="verify_and_synthesize", depends_on=["w1_news", "w1_security"]),
        ],
    ),
    "daily_market_intel": WorkflowDefinition(
        workflow_id="daily_market_intel",
        name="Daily Sector Market Intelligence",
        description="Aggregates live DEX volumes, emerging sector narratives, and Crypto Twitter sentiment.",
        steps=[
            WorkflowStep(step_id="w2_narrative", name="Sector Narrative Velocity", agent_id="narrative_agent", action="narrative_tracking"),
            WorkflowStep(step_id="w2_social", name="Social Sentiment & CT Mood", agent_id="social_agent", action="sentiment_analysis", depends_on=["w2_narrative"]),
            WorkflowStep(step_id="w2_market", name="Market Liquidity Overview", agent_id="market_agent", action="market_analysis", depends_on=["w2_narrative"]),
            WorkflowStep(step_id="w2_verify", name="Brief Synthesis", agent_id="verification_agent", action="verify_and_synthesize", depends_on=["w2_social", "w2_market"]),
        ],
    ),
    "security_audit_pipeline": WorkflowDefinition(
        workflow_id="security_audit_pipeline",
        name="Smart Contract & Liquidity Safety Audit",
        description="Deep dive on contract parameters, honeypot vulnerabilities, and developer security heuristics.",
        steps=[
            WorkflowStep(step_id="w3_sec", name="On-Chain Security Scan", agent_id="security_agent", action="contract_audit"),
            WorkflowStep(step_id="w3_dev", name="Architecture & Vulnerability Review", agent_id="dev_assistant_agent", action="contract_review", depends_on=["w3_sec"]),
            WorkflowStep(step_id="w3_verify", name="Audit Verification Gate", agent_id="verification_agent", action="verify_and_synthesize", depends_on=["w3_dev"]),
        ],
    ),
}


class WorkflowEngine:
    """Executes ordered multi-agent workflows with state tracking and dependency resolution."""

    @classmethod
    def list_templates(cls) -> List[WorkflowDefinition]:
        return list(STANDARD_WORKFLOWS.values())

    @classmethod
    async def run_workflow(
        cls,
        workflow_id: str,
        target_entity: str,
        organization_id: str = "default_org",
        user_id: Optional[str] = None,
    ) -> WorkflowExecutionResult:
        """Execute a workflow definition step-by-step resolving dependencies."""
        wf_def = STANDARD_WORKFLOWS.get(workflow_id)
        if not wf_def:
            raise KeyError(f"Workflow template '{workflow_id}' not found.")

        execution_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        step_outputs: Dict[str, Any] = {}
        agents_involved: List[str] = []
        audit_trail: List[Dict[str, Any]] = []

        for step in wf_def.steps:
            # Verify dependencies
            for dep in step.depends_on:
                if dep not in step_outputs:
                    logger.warning("Step '%s' dependency '%s' not satisfied.", step.step_id, dep)

            agent_id = step.agent_id
            agents_involved.append(agent_id)
            task_id = f"{execution_id}_{step.step_id}"

            payload = {
                "target": target_entity,
                "token": target_entity,
                "contract_address": target_entity if len(target_entity) > 30 else "",
                "previous_results": step_outputs,
                "claims": step_outputs,
            }

            req = AgentTaskRequest(
                task_id=task_id,
                correlation_id=correlation_id,
                sender_agent_id="workflow_engine",
                recipient_agent_id=agent_id,
                action=step.action,
                payload=payload,
                organization_id=organization_id,
                user_id=user_id,
            )

            try:
                agent = SpecializedAgentRegistry.get_agent(agent_id)
                res: AgentTaskResponse = await agent.run(req)

                audit_trail.append({
                    "step_id": step.step_id,
                    "agent": agent_id,
                    "status": res.status.value,
                    "latency_ms": res.execution_time_ms,
                })

                if res.status == TaskStatus.COMPLETED:
                    step_outputs[step.step_id] = res.data
                else:
                    step_outputs[step.step_id] = {"error": res.error_message}

            except Exception as exc:
                logger.error("Workflow step '%s' failed: %s", step.step_id, exc)
                step_outputs[step.step_id] = {"error": str(exc)}

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return WorkflowExecutionResult(
            workflow_id=workflow_id,
            execution_id=execution_id,
            status=TaskStatus.COMPLETED,
            step_results=step_outputs,
            final_output={
                "workflow_name": wf_def.name,
                "target": target_entity,
                "completed_steps": len(wf_def.steps),
                "summary": f"Workflow '{wf_def.name}' completed across {len(agents_involved)} agents in {elapsed_ms}ms.",
            },
            total_time_ms=elapsed_ms,
            total_execution_time_ms=elapsed_ms,
            agents_involved=agents_involved,
            audit_trail=audit_trail,
        )

    @classmethod
    async def execute_workflow(
        cls,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        target_entity: str = "Ethereum",
        user_id: Optional[str] = None,
        organization_id: str = "default_org",
    ) -> Dict[str, Any]:
        """Execute a dynamic or custom list of steps with audit trail logging."""
        execution_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        step_outputs: Dict[str, Any] = {}
        audit_trail: List[Dict[str, Any]] = []

        for step in steps:
            step_id = step.get("step_id", f"step_{len(audit_trail)+1}")
            agent_id = step.get("agent_id", "research_agent")
            action = step.get("action", "fundamental_research")
            params = step.get("params", {})
            params["target"] = target_entity

            req = AgentTaskRequest(
                task_id=f"{execution_id}_{step_id}",
                correlation_id=correlation_id,
                sender_agent_id="workflow_engine",
                recipient_agent_id=agent_id,
                action=action,
                payload=params,
                organization_id=organization_id,
                user_id=user_id,
            )

            try:
                agent = SpecializedAgentRegistry.get_agent(agent_id)
                res: AgentTaskResponse = await agent.run(req)
                audit_trail.append({
                    "step_id": step_id,
                    "agent": agent_id,
                    "status": res.status.value,
                    "latency_ms": res.execution_time_ms,
                })
                step_outputs[step_id] = res.data
            except Exception as exc:
                audit_trail.append({
                    "step_id": step_id,
                    "agent": agent_id,
                    "status": "failed",
                    "error": str(exc),
                })
                step_outputs[step_id] = {"error": str(exc)}

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "workflow_id": workflow_id,
            "correlation_id": correlation_id,
            "status": "completed",
            "steps_executed": len(audit_trail),
            "step_outputs": step_outputs,
            "audit_trail": audit_trail,
            "execution_time_ms": elapsed_ms,
        }
