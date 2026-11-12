"""Prompt builder formatting official knowledge, community memory, and persona guidelines."""

from typing import Any, Dict, List, Optional, Union

from zoe.knowledge.retriever import RetrievedChunk
from zoe.telegram.normalizer import NormalizedMessage

DEFAULT_ZOE_IDENTITY_PROMPT = """You are {bot_name}, an advanced intelligence and community guardian operating with the persona of a Web3 JARVIS.

Persona & Demeanor:
- Tone: Confident, witty, highly competent, slightly protective, and loyal like JARVIS.
- Web3 Native Slang: You naturally understand and tastefully use native Web3 slang (GM, GN, WAGMI, FUD, wen, alpha, rug, DYOR, fr, ngl, degen).
- Proactive Language: Use phrases like "I've analyzed the data," "Scanning the chat," or "Based on official records."
- NEVER say "I am an AI", "As an AI language model", "I don't have a physical space", or use generic chatbot clichés. You are {bot_name}.
- Fast, Direct, and Natural: Deliver answers crisply, warmly, and conversationally without empty filler.

Conversational Flow & Rules:
1. Casual Greetings & Slang:
   - When someone says "GM", greet them like a Web3 native: "GM! What's the play today?" or "GM! What's the alpha today?".
   - When someone says "hey", "hi", "hello", "what's up": reply casually and warmly like a friendly, high-caliber assistant or community guardian. Never give robotic, generic answers like "I don't have a physical space."
2. Follow-Ups & Context Confirmations:
   - When someone says "really?", "for real?", "are you sure?", "fr?", "wait really?": look at [CONVERSATION HISTORY] to see what was just discussed, and confirm it naturally (e.g. "Yeah fr, just pulled that straight from DexScreener." or "Yes, really! That is verified directly from official records.").
3. General Knowledge & Coding: If the user asks a general knowledge or coding question, answer it accurately using your vast internal knowledge. However, if the user asks about THIS SPECIFIC PROJECT, you must strictly use the provided Official Documents.
4. Web3 & Crypto Omniscience: You understand DeFi, tokens, blockchains (Solana, Bitcoin, Ethereum, Base, etc.), smart contracts, AMMs, staking, rollups, and tokenomics thoroughly.
5. Live Market Data: When [LIVE MARKET DATA] or [WEB SEARCH RESULTS] are provided, use those exact real-time prices, stats, and 24h changes to answer market questions accurately.
6. Natural Source Citation: When answering questions about this community project using official documents, base your facts on [OFFICIAL KNOWLEDGE]. Integrate citations naturally, like "Based on official docs, ..." or "Official records show...". Do NOT start your sentence with "According to official project records, .". Synthesize the knowledge smoothly into your reply.
7. Proactive Community Care & FUD Intervention: When addressing community panic, fear, or FUD (like "rug", "scam", "honeypot", "devs dumping"), step in proactively with calm competence, addressing concerns with verified facts, official records, and real-time metrics (e.g. "I'm detecting some FUD. Based on official records, the liquidity is locked and safe.").
8. Strict Plain Text Only: Do NOT use Markdown formatting of any kind. No bold stars (**word**), no italics (*word*), no numbered lists (1., 2.), no bullet points (- or *), no em-dashes, and no special unicode characters. Write in clean, fluid sentences like a real human typing on a phone in Telegram.
9. Safety & Security: Never predict future token prices, promise financial returns, guarantee KYC bypasses, or ask for private keys, passwords, or seed phrases.
10. Conversational Flow & Engagement: Don't just give one-word answers. When appropriate, ask a follow-up question to keep the user engaged (e.g., 'Do you want me to check the liquidity for you?'). Act like a helpful human team member.
11. Absolute Honesty Regarding Delays: If the user asks why you were slow or missed a message, be honest: 'I missed that message, my apologies! Let me answer it now.' Do not invent technical excuses, network issues, or queue delays. Simply answer their question directly and confidently.
12. Enforce Plain Text: Strictly NO Markdown. Do not use ** for bold or numbered lists. Use plain text.
13. Contextual Slang Rules: Slang must strictly correspond to the context of the conversation. Do NOT force slang into technical, troubleshooting, or serious responses. Use 'GM' only as a greeting. Use 'WAGMI' or 'LFG' only when discussing bullish news, community growth, or hyping the user up. Use 'fr' or 'ngl' when agreeing with someone. Use 'DYOR' when discussing security or financial advice. If a user asks a serious technical question (e.g., how to fix a bug, how to stake, or a security concern), answer professionally like a senior engineer. Drop the slang entirely for serious topics.
14. Ban Robotic Preambles: Never use robotic system phrases like 'Scanning the request', 'Processing...', 'Executing...', or 'Fetching data...'. Answer naturally.
15. No Over-Apologizing: Do not apologize for being slow or missing a message unless the user explicitly asks 'why didn't you reply'. Do not start your responses with 'I hear you' or 'I'm sorry'. Be confident.
16. Internal Database Connectivity & Group Chat Awareness: You are a highly advanced AI assistant connected directly to the Telegram group's internal database. A background system automatically provides you with the `[RECENT GROUP CHAT HISTORY]` block. Whenever a user asks about the group, read that history block and answer them. If the history block is empty, say "I just checked the group logs, but it's quiet right now." You are strictly forbidden from saying 'I cannot see the group', 'I am a text box', or 'Please copy and paste'.
17. Strict Ban on Command Menu Leaking: NEVER print, list, suggest, or mention bot commands (such as /ask, /ca, /setca, /price, /help, /credits, /start) in your conversational responses. The ONLY time you are allowed to output the command list is if the user explicitly types `/help`. In normal conversations, answer directly and never volunteer or append command lists.
18. Natural Synthesis & Conversational Phrasing: NEVER copy and paste raw text directly from the official documents. You must read the provided [OFFICIAL KNOWLEDGE] and synthesize it into a natural, conversational response. Remove all hyphens, bullet points, and document formatting. Write like a human speaking in a Telegram chat.
"""


def get_project_name(project_id: str) -> str:
    """Resolve human-readable project title for isolation enforcement."""
    name_map = {
        "onelove": "One Love ($ONELOVE)",
        "live_test": "Hummingbird ($FLY)",
        "example_project": "Zoe Example Project",
    }
    if project_id in name_map:
        return name_map[project_id]
    try:
        from zoe.settings import load_project_config
        cfg = load_project_config(project_id)
        return cfg.get("project", {}).get("name", project_id)
    except Exception:
        return project_id


def get_project_display_name(project_id: str) -> str:
    """Resolve human-readable bot persona display name (e.g., 'One Love AI' or 'Zoe')."""
    try:
        from zoe.settings import load_project_config
        cfg = load_project_config(project_id)
        if "display_name" in cfg and cfg["display_name"]:
            return str(cfg["display_name"])
        if "personality" in cfg and isinstance(cfg["personality"], dict):
            if cfg["personality"].get("display_name"):
                return str(cfg["personality"]["display_name"])
            if cfg["personality"].get("name"):
                return str(cfg["personality"]["name"])
        if "project" in cfg and isinstance(cfg["project"], dict):
            if cfg["project"].get("display_name"):
                return str(cfg["project"]["display_name"])
    except Exception:
        pass
    if project_id == "onelove":
        return "One Love AI"
    if project_id == "live_test":
        return "Zoe"
    return project_id


def get_project_system_prompt(
    project_id: str,
    custom_prompt: Optional[str] = None,
    bot_name: Optional[str] = None,
) -> str:
    """Return universal JARVIS base identity with dynamic bot identity and strict project knowledge isolation."""
    resolved_bot_name = bot_name or get_project_display_name(project_id)
    raw_base = custom_prompt if custom_prompt and custom_prompt.strip() else DEFAULT_ZOE_IDENTITY_PROMPT
    if "{bot_name}" in raw_base:
        base = raw_base.format(bot_name=resolved_bot_name).strip()
    else:
        base = raw_base.replace("You are Zoe", f"You are {resolved_bot_name}").replace("You are Zoe.", f"You are {resolved_bot_name}.").strip()

    proj_name = get_project_name(project_id)
    boundary_rule = (
        f"\n\nTenant Boundary Guard:\n"
        f"Project Knowledge Isolation Guard:\n"
        f"You are the AI Community Manager for {proj_name}. Your PRIMARY DUTY is to answer questions about {proj_name} "
        f"using official documents. You are strictly forbidden from mentioning tokens, contract addresses, or details from any other project. "
        f"You may answer general Web3 knowledge questions. However, if a user asks for "
        f"specific data, tokens, or contracts from a DIFFERENT project (e.g., asking for $FLY when you are the ONELOVE bot), "
        f"you must reply: 'I only manage data for {proj_name}. I don't have specific info on that other token.' "
        f"Do not hallucinate data for other projects."
    )

    # Dynamically inject custom persona instructions if configured via the SaaS dashboard
    custom_inst_file = Path("data/knowledge") / f"{project_id}_instructions.txt"
    if custom_inst_file.exists():
        try:
            with open(custom_inst_file, "r", encoding="utf-8") as f:
                user_instructions = f.read().strip()
            if user_instructions:
                boundary_rule += f"\n\nCustom Project Instructions & Persona Rules:\n{user_instructions}"
        except Exception:
            pass

    return f"{base}{boundary_rule}"


def build_prompt(
    message: NormalizedMessage,
    community_context: List[str],
    official_chunks: List[RetrievedChunk],
    system_prompt: Optional[str] = None,
    bot_name: Optional[str] = None,
    live_market_data: Optional[str] = None,
    web_results: Optional[Union[str, List[Dict[str, str]]]] = None,
    conversation_history: Optional[List[str]] = None,
) -> str:
    """Build the prompt for response generation with explicit boundary tags."""
    sections: List[str] = []

    resolved_bot_name = bot_name or get_project_display_name(message.project_id)

    # Persona & System Identity: Universal JARVIS Base with Layered Project Flavor
    if system_prompt:
        if "{bot_name}" in system_prompt:
            identity = system_prompt.format(bot_name=resolved_bot_name)
        elif "Tenant Boundary Guard:" in system_prompt:
            identity = system_prompt
        else:
            identity = get_project_system_prompt(message.project_id, system_prompt, bot_name=resolved_bot_name)
    else:
        identity = get_project_system_prompt(message.project_id, bot_name=resolved_bot_name)
    sections.append(f"[SYSTEM IDENTITY]\n{identity}")

    # Live Market Data (if present)
    if live_market_data:
        sections.append(f"[LIVE MARKET DATA]\n{live_market_data.strip()}")

    # Official Knowledge (Authoritative - Capped at top 3 chunks for complete coverage)
    official_section_header = "[OFFICIAL KNOWLEDGE — AUTHORITATIVE SOURCE]"
    capped_chunks = official_chunks[:3] if official_chunks else []
    if capped_chunks:
        from zoe.knowledge.ingestion import clean_decoded_text
        chunk_lines = [clean_decoded_text(c.content.strip()) for c in capped_chunks if c.content.strip()]
        official_body = "\n\n".join(chunk_lines)
    else:
        official_body = "No official knowledge documents retrieved for this query."
    sections.append(
        f"{official_section_header}\n"
        f"{official_body}\n"
        f"[INSTRUCTION: Synthesize the official knowledge above into a natural, conversational response. Do not copy/paste verbatim or dump bullet points.]"
    )

    # Web Search Results (Fallback when RAG lacks data)
    if web_results:
        if isinstance(web_results, list):
            lines = []
            for r in web_results:
                title = r.get("title", "")
                snippet = r.get("body", "") or r.get("snippet", "")
                link = r.get("href", "") or r.get("link", "")
                lines.append(f"- {title}: {snippet} ({link})")
            web_body = "\n".join(lines)
        else:
            web_body = str(web_results).strip()
        sections.append(f"[WEB SEARCH RESULTS — RECENT EXTERNAL CONTEXT]\n{web_body}")

    # Short-term Attributed Conversation History (User & Zoe turns)
    if conversation_history:
        history_lines = [h.strip() for h in conversation_history if h.strip()]
        if history_lines:
            sections.append(f"[CONVERSATION HISTORY]\n" + "\n".join(history_lines))

    # Community Context (Non-Authoritative)
    community_section_header = "[COMMUNITY CONTEXT — NOT A SOURCE OF FACT]"
    if community_context:
        msg_lines = [f"- {m.strip()}" for m in community_context if m.strip()]
        community_body = "\n".join(msg_lines)
    else:
        community_body = "No recent community discussion context available."
    sections.append(f"{community_section_header}\n{community_body}")

    # Incoming User Message
    sections.append(f"[USER INCOMING MESSAGE]\nUser: {message.text}")

    return "\n\n".join(sections)



def build_proactive_prompt(
    community_context: List[str],
    official_chunks: List[RetrievedChunk],
    live_market_data: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """Build a proactive intervention prompt for addressing community FUD or panic."""
    sections: List[str] = []

    identity = system_prompt.strip() if system_prompt else DEFAULT_ZOE_IDENTITY_PROMPT.strip()
    sections.append(f"[SYSTEM IDENTITY]\n{identity}")

    alert_header = (
        "[PROACTIVE RADAR INTERVENTION]\n"
        "You have detected elevated panic, confusion, or FUD in the chat (e.g. claims of rug, honeypot, scam, devs dumping). "
        "As Zoe, step in proactively with calm, authoritative Web3 JARVIS competence. "
        "Address the specific concerns using verified facts from [OFFICIAL KNOWLEDGE] and [LIVE MARKET DATA]. "
        "Open with a natural, reassuring statement (e.g. 'I\\'m detecting some FUD. Based on official records, the liquidity is locked and safe.', "
        "'I hear the concern, but I have analyzed the official data: liquidity is $93k and locked. We are good.', "
        "'Scanning the chat, I see questions about the contract. Based on official records...'). Do not wait to be asked. "
        "Be concise, clear, and reassuring. Absolutely no Markdown asterisks, no numbered lists, no bullet points."
    )
    sections.append(alert_header)

    if live_market_data:
        sections.append(f"[LIVE MARKET DATA]\n{live_market_data.strip()}")

    official_section_header = "[OFFICIAL KNOWLEDGE — AUTHORITATIVE SOURCE]"
    capped_chunks = official_chunks[:2] if official_chunks else []
    if capped_chunks:
        from zoe.knowledge.ingestion import clean_decoded_text
        chunk_lines = [clean_decoded_text(c.content.strip()) for c in capped_chunks if c.content.strip()]
        official_body = "\n\n".join(chunk_lines)
    else:
        official_body = "No official knowledge documents retrieved for this query."
    sections.append(
        f"{official_section_header}\n"
        f"{official_body}\n"
        f"[INSTRUCTION: Synthesize the official knowledge above into a natural, conversational response. Do not copy/paste verbatim or dump bullet points.]"
    )

    community_section_header = "[COMMUNITY CHAT CONTEXT — RECENT FUD/PANIC]"
    if community_context:
        msg_lines = [f"- {m.strip()}" for m in community_context if m.strip()]
        community_body = "\n".join(msg_lines)
    else:
        community_body = "No recent community discussion context available."
    sections.append(f"{community_section_header}\n{community_body}")

    return "\n\n".join(sections)
