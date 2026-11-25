"""Agent Memory Manager with strict multi-tenant boundary isolation and scoped retention."""

import time
from typing import Any, Dict, List, Optional
from zoe.agents.security import AgentSecurityException, AgentSecurityPolicy
from zoe.utils.logging import get_logger

logger = get_logger("zoe.agents.memory")


class AgentMemoryManager:
    """Manages scoped memories ensuring multi-tenant isolation across organizations and projects."""

    def __init__(self):
        # Scoped stores:
        # Task context: task_id -> Dict
        self._task_memory: Dict[str, Dict[str, Any]] = {}
        # Session memory: (org_id, session_id) -> List[Dict]
        self._session_memory: Dict[str, List[Dict[str, Any]]] = {}
        # Project memory: (org_id, project_id) -> Dict[str, Any]
        self._project_memory: Dict[str, Dict[str, Any]] = {}
        # User preferences: user_id -> Dict
        self._user_preferences: Dict[str, Dict[str, Any]] = {}

    def set_task_context(
        self,
        task_id: str,
        organization_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Store intermediate scratchpad state for a running task."""
        if not organization_id:
            raise AgentSecurityException("organization_id is required to set task context.")

        if task_id not in self._task_memory:
            self._task_memory[task_id] = {
                "organization_id": organization_id,
                "data": {},
                "created_at": time.time(),
            }

        # Check tenant boundary
        current_org = self._task_memory[task_id]["organization_id"]
        AgentSecurityPolicy.assert_organization_isolation(organization_id, current_org, "task memory")

        self._task_memory[task_id]["data"][key] = value

    def get_task_context(
        self,
        task_id: str,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Retrieve task intermediate scratchpad with tenant isolation."""
        entry = self._task_memory.get(task_id)
        if not entry:
            return {}

        current_org = entry.get("organization_id", "global")
        AgentSecurityPolicy.assert_organization_isolation(organization_id, current_org, "task memory")

        return entry.get("data", {})

    def add_session_message(
        self,
        session_id: str,
        organization_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append to session conversation memory."""
        key = f"{organization_id}:{session_id}"
        if key not in self._session_memory:
            self._session_memory[key] = []

        sanitized = AgentSecurityPolicy.sanitize_untrusted_content(content)
        self._session_memory[key].append({
            "role": role,
            "content": sanitized,
            "timestamp": time.time(),
        })

        # Cap session history to 20 messages
        if len(self._session_memory[key]) > 20:
            self._session_memory[key] = self._session_memory[key][-20:]

    def get_session_history(
        self,
        session_id: str,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """Retrieve session history ensuring organization isolation."""
        key = f"{organization_id}:{session_id}"
        return self._session_memory.get(key, [])

    def save_task_summary(
        self,
        organization_id: str,
        agent_id: str,
        summary: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Persist long-term project/task summary with organization boundary."""
        if not organization_id:
            raise AgentSecurityException("organization_id is required to persist memory.")

        key = f"{organization_id}:{agent_id}"
        if key not in self._project_memory:
            self._project_memory[key] = []

        sanitized = AgentSecurityPolicy.sanitize_untrusted_content(summary)
        self._project_memory[key].append({
            "summary": sanitized,
            "session_id": session_id,
            "timestamp": time.time(),
        })

    def get_organization_memory(
        self,
        organization_id: str,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve long-term organization memory ensuring no cross-tenant leakage."""
        if not organization_id:
            return []

        results = []
        if agent_id:
            key = f"{organization_id}:{agent_id}"
            results.extend(self._project_memory.get(key, []))
        else:
            for k, items in self._project_memory.items():
                if k.startswith(f"{organization_id}:"):
                    results.extend(items)
        return results[-limit:]

    def clear_task_memory(self, task_id: str) -> None:
        """Clean up ephemeral memory upon task completion."""
        self._task_memory.pop(task_id, None)
