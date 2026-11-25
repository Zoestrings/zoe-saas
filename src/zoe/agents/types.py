"""Type definitions and schemas for the Zoe Autonomous Agent ecosystem."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SecurityLevel(str, Enum):
    READ_ONLY = "read_only"
    ANALYTICS = "analytics"
    OPERATIONAL = "operational"
    ADMIN = "admin"


class AgentTaskRequest(BaseModel):
    task_id: str
    parent_task_id: Optional[str] = None
    correlation_id: str
    sender_agent_id: str
    recipient_agent_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 2
    organization_id: str = "default_org"
    project_id: Optional[str] = None
    user_id: Optional[str] = None


class AgentTaskResponse(BaseModel):
    task_id: str
    correlation_id: str
    agent_id: str
    status: TaskStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_consumed: int = 0
    tools_called: List[str] = Field(default_factory=list)
    confidence_score: float = 1.0


class AgentConfig(BaseModel):
    agent_id: str
    name: str
    description: str
    category: str = "intelligence"
    capabilities: List[str] = Field(default_factory=list)
    approved_tools: List[str] = Field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.READ_ONLY
    system_prompt: Optional[str] = None
    max_steps: int = 5
    timeout_seconds: int = 30
    is_custom: bool = False
    organization_id: str = "global"
    is_active: bool = True
    credit_cost_per_call: int = 1


class ToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    category: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    permission_required: SecurityLevel = SecurityLevel.READ_ONLY
    timeout_seconds: int = 15
    cost_credits: int = 1


class WorkflowStep(BaseModel):
    step_id: str
    name: str
    agent_id: str
    action: str
    input_template: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    timeout_seconds: int = 120
    organization_id: str = "default_org"
    created_by: Optional[str] = None


class WorkflowExecutionResult(BaseModel):
    workflow_id: str
    execution_id: str
    status: TaskStatus
    step_results: Dict[str, Any] = Field(default_factory=dict)
    final_output: Dict[str, Any] = Field(default_factory=dict)
    total_time_ms: float = 0.0
    total_execution_time_ms: float = 0.0
    final_synthesis: str = ""
    agents_involved: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None


class OrchestrationPlan(BaseModel):
    plan_id: str
    goal: str
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_steps: int = 1
    selected_agents: List[str] = Field(default_factory=list)
