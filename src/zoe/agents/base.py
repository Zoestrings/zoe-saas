"""Base agent interface for standardized, secure Zoe autonomous agents."""

import abc
import time
from typing import Any, Dict, List, Optional
from zoe.agents.types import (
    AgentConfig,
    AgentStatus,
    AgentTaskRequest,
    AgentTaskResponse,
    SecurityLevel,
    TaskStatus,
)
from zoe.agents.security import AgentSecurityPolicy
from zoe.agents.tools_registry import ToolRegistry
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.base")


class BaseAgent(abc.ABC):
    """Abstract base class representing a specialized Zoe autonomous agent."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        approved_tools: List[str],
        security_level: SecurityLevel = SecurityLevel.READ_ONLY,
        system_prompt: Optional[str] = None,
        max_steps: int = 5,
        timeout_seconds: int = 30,
        organization_id: str = "global",
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.approved_tools = approved_tools
        self.security_level = security_level
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.organization_id = organization_id
        self.status = AgentStatus.IDLE

        # Telemetry metrics
        self.total_invocations: int = 0
        self.successful_invocations: int = 0
        self.failed_invocations: int = 0
        self.total_execution_time_ms: float = 0.0

    @property
    def config(self) -> AgentConfig:
        """Return standardized configuration representation."""
        return self.get_config()

    def get_config(self) -> AgentConfig:
        """Return standardized configuration representation."""
        return AgentConfig(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
            approved_tools=self.approved_tools,
            security_level=self.security_level,
            system_prompt=self.system_prompt,
            max_steps=self.max_steps,
            timeout_seconds=self.timeout_seconds,
            organization_id=self.organization_id,
            is_active=self.status != AgentStatus.DISABLED,
        )

    async def execute_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        organization_id: str = "default_org",
    ) -> Dict[str, Any]:
        """Execute a tool authorized for this agent."""
        if tool_id not in self.approved_tools:
            raise PermissionError(
                f"Agent '{self.agent_id}' is not authorized to call tool '{tool_id}'. "
                f"Approved tools: {self.approved_tools}"
            )
        return await ToolRegistry.execute_tool(
            tool_id=tool_id,
            params=params,
            agent_id=self.agent_id,
            organization_id=organization_id,
        )

    async def run(self, request: AgentTaskRequest) -> AgentTaskResponse:
        """Execute the task request with boundary enforcement, timing, and error handling."""
        start_time = time.time()
        self.status = AgentStatus.BUSY
        self.total_invocations += 1

        # 1. Security policy validation
        is_valid, sec_error = AgentSecurityPolicy.validate_task_request(
            action=request.action,
            payload=request.payload,
            organization_id=request.organization_id,
            allowed_tools=self.approved_tools,
        )
        if not is_valid:
            self.status = AgentStatus.IDLE
            self.failed_invocations += 1
            return AgentTaskResponse(
                task_id=request.task_id,
                correlation_id=request.correlation_id,
                agent_id=self.agent_id,
                status=TaskStatus.FAILED,
                error_message=sec_error or "Security policy rejection",
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        # 2. Execute agent implementation
        try:
            output_data, tools_used = await self._process_task(request)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            self.status = AgentStatus.IDLE
            self.successful_invocations += 1
            self.total_execution_time_ms += elapsed_ms

            return AgentTaskResponse(
                task_id=request.task_id,
                correlation_id=request.correlation_id,
                agent_id=self.agent_id,
                status=TaskStatus.COMPLETED,
                data=output_data,
                execution_time_ms=elapsed_ms,
                tools_called=tools_used,
                confidence_score=0.95,
            )
        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            self.status = AgentStatus.IDLE
            self.failed_invocations += 1
            self.total_execution_time_ms += elapsed_ms
            logger.error("Agent '%s' failed on task '%s': %s", self.agent_id, request.task_id, exc)

            return AgentTaskResponse(
                task_id=request.task_id,
                correlation_id=request.correlation_id,
                agent_id=self.agent_id,
                status=TaskStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed_ms,
            )

    @abc.abstractmethod
    async def _process_task(
        self, request: AgentTaskRequest
    ) -> tuple[Dict[str, Any], List[str]]:
        """Core specialized processing logic to be implemented by each agent."""
        pass
