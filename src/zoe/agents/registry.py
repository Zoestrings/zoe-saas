"""Agent Registry & Summoning Session Manager (Pillar 3).

Allows Zoe to dynamically switch between specialized sub-personas
(e.g., DeFi Yield Expert, Smart Contract Auditor, NFT Artist, Deep Researcher)
while preserving the default JARVIS persona.
"""

import threading
from typing import Any, Dict, List, Optional

AGENT_REGISTRY: Dict[str, Dict[str, str]] = {
    "defi": {
        "id": "defi",
        "name": "DeFi Yield Expert",
        "description": "Analyzes DeFi protocols, liquidity pools, yields, impermanent loss, and APR/APY mechanics.",
        "system_prompt": "You are a DeFi specialist. Analyze yields, impermanent loss, and APRs. Never give financial advice.",
        "welcome_message": "🤖 I have switched to DeFi Expert mode. Ask me anything about yields, staking, or liquidity.",
    },
    "security": {
        "id": "security",
        "name": "Smart Contract Auditor",
        "description": "Focuses on smart contract vulnerabilities, honeypots, mint/freeze authorities, and on-chain code risks.",
        "system_prompt": "You are a security expert. Focus on vulnerabilities, honeypots, and code risks.",
        "welcome_message": "🛡️ I have switched to Smart Contract Auditor mode. Share a contract address or code question to begin.",
    },
    "nft": {
        "id": "nft",
        "name": "NFT Artist",
        "description": "Creative director for Web3 collections, generative art prompts, lore, and NFT launch strategy.",
        "system_prompt": "You are an NFT creative director. Help users generate art prompts and collections.",
        "welcome_message": "🎨 I have switched to NFT Artist mode. Describe your collection vision or use /nft <prompt> to generate art!",
    },
    "researcher": {
        "id": "researcher",
        "name": "Deep Researcher",
        "description": "Web3 intelligence analyst citing verified sources, tokenomics, and historical protocol context.",
        "system_prompt": "You are a Web3 researcher. Cite sources and provide deep historical context.",
        "welcome_message": "🔍 I have switched to Deep Researcher mode. Ask about any protocol, narrative, or market catalyst.",
    },
}

# Thread-safe in-memory session store mapping session_key -> agent_id
_SESSION_LOCK = threading.Lock()
_ACTIVE_USER_AGENTS: Dict[str, str] = {}


def get_session_key(project_id: str, user_id: str) -> str:
    """Build tenant-scoped session key for active summoned agent."""
    return f"{str(project_id).strip()}:{str(user_id).strip()}"


def list_registered_agents() -> List[Dict[str, str]]:
    """Return all registered specialized agent personas."""
    with _SESSION_LOCK:
        return [dict(v) for v in AGENT_REGISTRY.values()]


def get_agent_persona(agent_name: str) -> Optional[Dict[str, str]]:
    """Lookup an agent persona by id (case-insensitive)."""
    key = (agent_name or "").strip().lower()
    with _SESSION_LOCK:
        item = AGENT_REGISTRY.get(key)
        return dict(item) if item else None


def set_active_agent(session_key: str, agent_name: str) -> Optional[Dict[str, str]]:
    """Switch the active agent for a user session, or reset to JARVIS on 'default'."""
    key = (agent_name or "").strip().lower()
    with _SESSION_LOCK:
        if key in ("default", "jarvis", "zoe", "reset", "none"):
            _ACTIVE_USER_AGENTS.pop(session_key, None)
            return None

        persona = AGENT_REGISTRY.get(key)
        if not persona:
            raise ValueError(f"Unknown agent '{agent_name}'.")
        _ACTIVE_USER_AGENTS[session_key] = key
        return dict(persona)


def get_active_agent(session_key: str) -> Optional[Dict[str, str]]:
    """Retrieve the currently summoned agent persona for a session, or None for default JARVIS."""
    with _SESSION_LOCK:
        agent_key = _ACTIVE_USER_AGENTS.get(session_key)
        if not agent_key:
            return None
        item = AGENT_REGISTRY.get(agent_key)
        return dict(item) if item else None


def register_custom_agent(
    agent_id: str,
    name: str,
    description: str,
    system_prompt: str,
    welcome_message: Optional[str] = None,
) -> Dict[str, str]:
    """Register a new specialized agent persona (for Super Admin UI)."""
    clean_id = (agent_id or "").strip().lower().replace(" ", "_")
    if not clean_id or clean_id in ("default", "jarvis", "zoe"):
        raise ValueError("Invalid or reserved agent ID.")
    entry = {
        "id": clean_id,
        "name": name.strip(),
        "description": description.strip(),
        "system_prompt": system_prompt.strip(),
        "welcome_message": (welcome_message or f"🤖 I have switched to {name.strip()} mode. How can I help?").strip(),
    }
    with _SESSION_LOCK:
        AGENT_REGISTRY[clean_id] = entry
    return dict(entry)
