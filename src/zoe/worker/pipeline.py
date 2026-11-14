"""Worker pipeline orchestrating classification, decision, retrieval, generation, safety, and outbox enqueue."""

from dataclasses import dataclass
from datetime import timedelta
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Callable, Dict, List, Optional, Union

from zoe.clock.clock import format_timestamp, now
from zoe.conversation.classifier import ClassificationResult, classify_message
from zoe.conversation.prompt_builder import (
    DEFAULT_ZOE_IDENTITY_PROMPT,
    build_proactive_prompt,
    build_prompt,
    get_project_system_prompt,
)
from zoe.conversation.intent import detect_contract_address
from zoe.conversation.router import route_intent
from zoe.conversation.sentiment import analyze_group_sentiment_sync
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.escalation.handler import EscalationResult, handle_escalation
from zoe.inbox.lifecycle import transition
from zoe.knowledge.retriever import search
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import (
    get_recent_context,
    get_recent_conversation_history,
    record_community_message,
)
from zoe.participation.decision import ParticipationDecision, should_respond
from zoe.safety.validator import SafetyResult, validate_output
from zoe.telegram.normalizer import NormalizedMessage
from zoe.tools.dexscreener import get_token_price_sync, search_token_price_sync
from zoe.tools.web_search import search_web_sync
from zoe.utils.logging import get_logger
from zoe.utils.sanitizer import clean_unnecessary_characters

logger = get_logger("zoe.worker.pipeline")


@dataclass
class PipelineResult:
    inbox_id: int
    responded: bool
    classification: ClassificationResult
    decision: ParticipationDecision
    outbox_id: Optional[int] = None
    response_text: Optional[str] = None
    safety_result: Optional[SafetyResult] = None
    escalation_result: Optional[EscalationResult] = None
    aborted: bool = False
    inline_keyboard: Optional[List[List[Dict[str, str]]]] = None


def extract_token_query(text: str, default_token: str = "$FLY") -> str:
    """Extract cryptocurrency symbol, name, or contract address from text."""
    ca_match = re.search(r"\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})\b", text)
    if ca_match:
        return ca_match.group(1)

    cashtag_match = re.search(r"\$([a-zA-Z0-9]+)", text)
    if cashtag_match:
        return cashtag_match.group(1).upper()

    match = re.search(
        r"\b(?:price\s+of|worth\s+of|how\s+much\s+is|value\s+of|rate\s+of|check)\s+([a-zA-Z0-9_-]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        token = match.group(1).strip()
        if token.lower() not in {"the", "a", "an", "this", "our", "your", "token"}:
            return token

    match2 = re.search(r"\b([a-zA-Z0-9_-]+)\s+price\b", text, re.IGNORECASE)
    if match2:
        token = match2.group(1).strip()
        if token.lower() not in {"the", "a", "an", "current", "token", "live"}:
            return token

    # Check for direct mentions of known major crypto assets or project terms
    common_tokens = [
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
        "dogecoin", "doge", "hummingbird", "fly", "humminb",
        "pepe", "shib", "bonk", "wif", "xrp", "ripple", "ada",
        "cardano", "bnb", "binance", "sui", "near", "trx", "tron",
        "link", "chainlink", "dot", "polkadot", "uni", "uniswap",
        "ltc", "litecoin", "matic", "pol", "polygon", "arb", "arbitrum"
    ]
    for coin in common_tokens:
        if re.search(rf"\b{coin}\b", text, re.IGNORECASE):
            return coin

    return default_token


def _safe_generate(
    client: Any,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 250,
    project_id: str = "default",
    is_technical: bool = False,
) -> str:
    """Invoke client.generate with max_tokens strictly capped at 250 and log latency."""
    import time
    # Hard cap at 250 tokens prevents overly long copy-pasted responses and Telegram timeouts
    effective_tokens = min(int(max_tokens) if max_tokens else 250, 250)

    t0 = time.perf_counter()
    try:
        resp = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=effective_tokens,
            is_technical=is_technical,
        )
    except TypeError:
        resp = client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    elapsed = time.perf_counter() - t0
    logger.info("[%s] LLM generation took: %.2f seconds (capped max_tokens=%d)", project_id, elapsed, effective_tokens)
    return resp


def process_message(
    inbox_row: Union[int, Dict[str, Any]],
    db_conns: Optional[Dict[str, sqlite3.Connection]] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    kb_db_path: Optional[Union[str, Path]] = None,
    mem_db_path: Optional[Union[str, Path]] = None,
    index_dir: Optional[Union[str, Path]] = None,
    llm_client: Optional[Any] = None,
    model: Optional[Any] = None,
    safety_validator_fn: Optional[Callable[..., SafetyResult]] = None,
    web_search_fn: Optional[Callable[[str], List[Dict[str, str]]]] = None,
    simulated: Optional[bool] = None,
    enforce_accuracy_guard: Optional[bool] = None,
    intent: Optional[str] = None,
) -> PipelineResult:
    """Run the complete pipeline: classify -> decide -> retrieve -> prompt -> generate -> safety -> outbox."""
    conns = db_conns or {}
    conn_op = conns.get("operational") or open_operational_db(
        op_db_path or "data/operational/operational.db"
    )
    conn_kb = conns.get("knowledge") or open_official_knowledge_db(
        kb_db_path or "data/official_knowledge/official_knowledge.db"
    )
    conn_mem = conns.get("memory") or open_community_memory_db(
        mem_db_path or "data/community_memory/community_memory.db"
    )

    close_conns = db_conns is None

    try:
        # 1. Fetch inbox row
        if isinstance(inbox_row, int):
            cur = conn_op.execute(
                """
                SELECT id, project_id, telegram_update_id, group_id, telegram_message_id,
                       pseudonymous_user_id, text, reply_to_message_id, is_forward,
                       message_timestamp, state
                FROM inbox_messages WHERE id = ?
                """,
                (inbox_row,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Inbox row {inbox_row} not found")
            inbox_id = row[0]
            project_id = row[1]
            update_id = row[2]
            group_id = row[3]
            msg_id = row[4]
            pseudo_id = row[5]
            text = row[6]
            reply_to_id = row[7]
            is_fwd = bool(row[8])
            msg_timestamp = row[9]
            state = row[10]
        else:
            inbox_id = inbox_row["id"]
            project_id = inbox_row["project_id"]
            update_id = inbox_row["telegram_update_id"]
            group_id = inbox_row["group_id"]
            msg_id = inbox_row["telegram_message_id"]
            pseudo_id = inbox_row["pseudonymous_user_id"]
            text = inbox_row["text"]
            reply_to_id = inbox_row.get("reply_to_message_id")
            is_fwd = bool(inbox_row.get("is_forward", 0))
            msg_timestamp = inbox_row["message_timestamp"]
            state = inbox_row.get("state", "processing")

        if state == "message_persisted":
            transition(conn_op, inbox_id, "processing")
            conn_op.commit()

        norm_msg = NormalizedMessage(
            project_id=project_id,
            telegram_update_id=update_id,
            group_id=group_id,
            telegram_message_id=msg_id,
            pseudonymous_user_id=pseudo_id,
            text=text,
            reply_to_message_id=reply_to_id,
            is_forward=is_fwd,
            timestamp=msg_timestamp,
        )

        # 2. Record to community memory
        record_community_message(
            project_id=norm_msg.project_id,
            group_id=norm_msg.group_id,
            telegram_message_id=norm_msg.telegram_message_id,
            pseudonymous_user_id=norm_msg.pseudonymous_user_id,
            content=norm_msg.text,
            received_at=norm_msg.timestamp,
            db_path=mem_db_path,
            conn=conn_mem,
        )

        # 3. Retrieve community context
        community_context = get_recent_context(
            project_id=norm_msg.project_id,
            group_id=norm_msg.group_id,
            limit=10,
            db_path=mem_db_path,
            conn=conn_mem,
        )

        # 3b. Retrieve short-term dialogue history (User and Zoe turns)
        conversation_history = get_recent_conversation_history(
            project_id=norm_msg.project_id,
            group_id=norm_msg.group_id,
            limit=6,
            db_path=mem_db_path,
            exclude_message_id=norm_msg.telegram_message_id,
            conn=conn_mem,
        )

        # 4. Classify message and determine intent
        intent_start = time.perf_counter()
        classification = classify_message(norm_msg.text, community_context, llm_client=llm_client)

        # 5. Check last response time and recent Zoe messages
        cur = conn_op.execute(
            """
            SELECT MAX(created_at) FROM participation_log
            WHERE project_id = ? AND group_id = ? AND decision = 'respond'
            """,
            (norm_msg.project_id, norm_msg.group_id),
        )
        last_row = cur.fetchone()
        last_resp_time = last_row[0] if last_row else None

        cur_zoe = conn_op.execute(
            """
            SELECT reply_to_message_id FROM outbox_messages
            WHERE project_id = ? AND group_id = ?
            ORDER BY id DESC LIMIT 5
            """,
            (norm_msg.project_id, norm_msg.group_id),
        )
        recent_zoe_msg_ids = [r[0] for r in cur_zoe.fetchall() if r[0]]

        # Load project config and module toggles from DB or config file
        respond_to_casual = False
        modules_cfg = {}
        try:
            row_proj = conn_op.execute(
                "SELECT config_json FROM projects WHERE project_id = ?",
                (norm_msg.project_id,),
            ).fetchone()
            if row_proj and row_proj[0]:
                p_cfg = json.loads(row_proj[0])
                respond_to_casual = p_cfg.get("participation", {}).get("respond_to_casual", False)
                modules_cfg = p_cfg.get("modules", {})
        except Exception as exc:
            logger.warning("Error loading config_json: %s", exc)

        if not modules_cfg:
            try:
                from zoe.settings import load_project_config
                cfg_file = load_project_config(norm_msg.project_id)
                modules_cfg = cfg_file.get("modules", {})
            except Exception:
                modules_cfg = {}

        module_comm_mgr = modules_cfg.get("community_manager", True)
        module_crypto_intel = modules_cfg.get("crypto_intelligence", True)
        module_comm_intel = modules_cfg.get("community_intelligence", True)

        if not module_comm_mgr and classification.category == "casual":
            respond_to_casual = False

        active_system_prompt = get_project_system_prompt(
            norm_msg.project_id,
            p_cfg.get("personality", {}).get("system_prompt") if "p_cfg" in locals() and isinstance(p_cfg, dict) else None,
        )

        # Force Group History Injection for Private Messages (DMs)
        # In Telegram, positive chat IDs indicate DMs (group IDs start with '-')
        is_dm = not str(norm_msg.group_id).startswith("-")
        dm_group_msgs = []
        if is_dm:
            target_group_id = None
            try:
                target_group_id = str(p_cfg.get("telegram", {}).get("group_id") or "")
            except Exception:
                pass
            if not target_group_id:
                try:
                    from zoe.settings import load_project_config
                    cfg_obj = load_project_config(norm_msg.project_id)
                    target_group_id = str(cfg_obj.get("telegram", {}).get("group_id") or "")
                except Exception:
                    pass

            from zoe.memory.short_term import get_recent_group_messages
            dm_group_msgs = get_recent_group_messages(
                project_id=norm_msg.project_id,
                target_group_id=target_group_id,
                limit=5,
                conn_op=conn_op,
                conn_mem=conn_mem,
            )

            from zoe.conversation.prompt_builder import get_project_display_name
            bot_display_name = get_project_display_name(norm_msg.project_id)
            if dm_group_msgs:
                history_entries = []
                for m in dm_group_msgs:
                    sender = bot_display_name if m.get("user_id") in ("zoe", "bot", norm_msg.project_id) else "Community Member"
                    history_entries.append(f"{sender}: {m['text'].strip()}")
                recent_group_block = "\n".join(history_entries)
            else:
                recent_group_block = "No recent group chat messages recorded in logs."

            group_history_system_block = (
                f"\n\n[RECENT GROUP CHAT HISTORY]\n"
                f"{recent_group_block}\n\n"
                f"Whenever the user asks about the group, read the [RECENT GROUP CHAT HISTORY] block above and answer them. "
                f"If the history block is empty or quiet, say 'I just checked the group logs, but it\\'s quiet right now.' "
                f"You are strictly forbidden from saying 'I cannot see the group', 'I am a text box', or 'Please copy and paste'."
            )
            active_system_prompt += group_history_system_block

        # 6. Decide participation
        current_msg_dt = None
        if norm_msg.timestamp:
            try:
                from zoe.clock.clock import parse_timestamp
                current_msg_dt = (
                    parse_timestamp(norm_msg.timestamp)
                    if isinstance(norm_msg.timestamp, str)
                    else norm_msg.timestamp
                )
            except Exception:
                current_msg_dt = None

        rate_limit_sec = 20.0
        try:
            if "rate_limit_seconds" in p_cfg.get("participation", {}):
                rate_limit_sec = float(p_cfg["participation"]["rate_limit_seconds"])
        except Exception:
            rate_limit_sec = 20.0

        bot_identity_name = p_cfg.get("personality", {}).get("name", "Zoe")
        decision = should_respond(
            message=norm_msg,
            classification=classification,
            recent_zoe_messages=recent_zoe_msg_ids,
            last_response_time=last_resp_time,
            current_time=current_msg_dt,
            db_conn=conn_op,
            rate_limit_seconds=rate_limit_sec,
            bot_name=bot_identity_name,
            respond_to_casual=respond_to_casual,
            llm_client=llm_client,
        )

        conn_op.execute(
            """
            UPDATE inbox_messages
            SET classification_category = ?, classification_confidence = ?, decision = ?, decision_reason = ?
            WHERE id = ?
            """,
            (classification.category, classification.confidence, decision.decision, decision.reason, inbox_id),
        )
        conn_op.commit()

        # 7. Check if escalation is triggered
        if classification.category == "escalation_trigger" or decision.decision == "escalate":
            esc_res = handle_escalation(
                inbox_row=inbox_id,
                reason=classification.reason or decision.reason,
                db_conns={"operational": conn_op},
            )
            return PipelineResult(
                inbox_id=inbox_id,
                responded=False,
                classification=classification,
                decision=decision,
                escalation_result=esc_res,
            )

        # 8. Check proactive sentiment radar (JARVIS Mode) - only if community_intelligence enabled
        sentiment = "calm"
        if module_comm_intel:
            sentiment = analyze_group_sentiment_sync(community_context, llm_client=llm_client)
        if sentiment == "panicked/fud":
            # 10-minute cooldown check (600 seconds)
            cur_cd = conn_op.execute(
                """
                SELECT MAX(created_at) FROM inbox_messages
                WHERE project_id = ? AND group_id = ? AND decision_reason = 'proactive_fud_intervention'
                """,
                (norm_msg.project_id, norm_msg.group_id),
            )
            row_cd = cur_cd.fetchone()
            proactive_cooldown_active = False
            if row_cd and row_cd[0]:
                try:
                    from zoe.clock.clock import parse_timestamp
                    last_fud_dt = parse_timestamp(row_cd[0])
                    if (now() - last_fud_dt).total_seconds() < 600.0:
                        proactive_cooldown_active = True
                except Exception:
                    pass

            if not proactive_cooldown_active:
                logger.info(
                    "Proactive Sentiment Radar triggered: sentiment='panicked/fud' for group %s. Overriding decision to proactive intervention.",
                    norm_msg.group_id,
                )
                decision = ParticipationDecision(
                    decision="respond",
                    should_respond=True,
                    reason="proactive_fud_intervention",
                )
                intent = "proactive_fud"
            elif not decision.should_respond:
                transition(conn_op, inbox_id, "no_response_required")
                conn_op.commit()
                return PipelineResult(
                    inbox_id=inbox_id,
                    responded=False,
                    classification=classification,
                    decision=decision,
                )
            else:
                if intent is None:
                    ca_detected = detect_contract_address(norm_msg.text)
                    intent = "crypto_intelligence" if ca_detected else route_intent(norm_msg.text)
                logger.info("Message %d routed to intent: '%s'", inbox_id, intent)
        elif not decision.should_respond:
            transition(conn_op, inbox_id, "no_response_required")
            conn_op.commit()
            return PipelineResult(
                inbox_id=inbox_id,
                responded=False,
                classification=classification,
                decision=decision,
            )
        else:
            # Route Intent (Tool Router)
            if intent is None:
                ca_detected = detect_contract_address(norm_msg.text)
                intent = "crypto_intelligence" if ca_detected else route_intent(norm_msg.text)
            logger.info("Message %d routed to intent: '%s'", inbox_id, intent)

        intent_time = round(time.perf_counter() - intent_start, 3)
        rag_time = 0.0
        llm_time = 0.0

        official_chunks = []
        web_results: List[Dict[str, str]] = []
        generated_text = None
        inline_keyboard: Optional[List[List[Dict[str, str]]]] = None
        cmd: Optional[str] = None

        # Command Interception (/ca, /price, /help, /ask, /credits, /add_credits, /start)
        cmd_match = re.match(r"^/([a-zA-Z0-9_]+)(?:@\w+)?(?:\s+(.*))?$", norm_msg.text.strip(), re.DOTALL)
        if cmd_match:
            cmd = cmd_match.group(1).lower()
            cmd_arg = (cmd_match.group(2) or "").strip()
            from zoe.conversation.prompt_builder import get_project_display_name, get_project_name

            if cmd == "ca":
                token_addr = None
                try:
                    from zoe.settings import load_project_config
                    p_cfg_obj = load_project_config(norm_msg.project_id)
                    token_addr = p_cfg_obj.get("token_address") or p_cfg_obj.get("project", {}).get("token_address")
                except Exception:
                    pass
                if not token_addr:
                    token_addr = p_cfg.get("token_address") or p_cfg.get("project", {}).get("token_address")
                proj_title = get_project_name(norm_msg.project_id)
                if token_addr:
                    from zoe.tools.crypto_intel import generate_ca_inline_keyboard, get_token_intel_sync
                    intel = get_token_intel_sync(token_address=token_addr, project_id=norm_msg.project_id)
                    generated_text = f"Here is the official contract address for {proj_title}:\n{token_addr}"
                    inline_keyboard = generate_ca_inline_keyboard(token_addr, intel, project_id=norm_msg.project_id)
                else:
                    generated_text = f"No contract address is configured for {proj_title}."
                intent = "command_ca"

            elif cmd == "price":
                token_addr = None
                try:
                    from zoe.settings import load_project_config
                    p_cfg_obj = load_project_config(norm_msg.project_id)
                    token_addr = p_cfg_obj.get("token_address") or p_cfg_obj.get("project", {}).get("token_address")
                except Exception:
                    pass
                if not token_addr:
                    token_addr = p_cfg.get("token_address") or p_cfg.get("project", {}).get("token_address")
                from zoe.tools.crypto_intel import format_token_intel_response, generate_ca_inline_keyboard, get_token_intel_sync
                intel = get_token_intel_sync(token_address=token_addr, project_id=norm_msg.project_id)
                generated_text = format_token_intel_response(intel)
                if token_addr:
                    inline_keyboard = generate_ca_inline_keyboard(token_addr, intel, project_id=norm_msg.project_id)
                intent = "command_price"

            elif cmd in ("credits", "balance"):
                bot_display_name = get_project_display_name(norm_msg.project_id)
                generated_text = f"Your {bot_display_name} balance is unlimited and fully active for this community. No top-up needed!"
                intent = "command_credits"

            elif cmd in ("add_credits", "topup"):
                bot_display_name = get_project_display_name(norm_msg.project_id)
                generated_text = f"Your community membership includes full access to {bot_display_name}. Top-ups are not required at this time."
                intent = "command_add_credits"

            elif cmd in ("links", "socials", "social"):
                proj_title = get_project_name(norm_msg.project_id)
                links_cfg = {}
                try:
                    from zoe.settings import load_project_config
                    p_cfg = load_project_config(norm_msg.project_id)
                    links_cfg = p_cfg.get("links", {})
                except Exception:
                    pass

                website_url = links_cfg.get("website", "https://www.onelovesailingcoin.com")
                twitter_url = links_cfg.get("twitter", "https://x.com/thecaptrobbie?s=11")
                telegram_url = links_cfg.get("telegram", "https://t.me/ONELOVECoinCrew")
                tiktok_url = links_cfg.get("tiktok", "https://www.tiktok.com/@captain.robbie")

                generated_text = (
                    f"Official Links & Socials for {proj_title}:\n\n"
                    f"🌐 Website: {website_url}\n"
                    f"🐦 Twitter / X: {twitter_url}\n"
                    f"✈️ Telegram: {telegram_url}\n"
                    f"🎵 TikTok: {tiktok_url}"
                )
                inline_keyboard = [
                    [
                        {"text": "🌐 Website", "url": website_url},
                        {"text": "🐦 Twitter / X", "url": twitter_url},
                    ],
                    [
                        {"text": "✈️ Telegram", "url": telegram_url},
                        {"text": "🎵 TikTok", "url": tiktok_url},
                    ],
                ]
                intent = "command_links"

            elif cmd == "help":
                bot_display_name = get_project_display_name(norm_msg.project_id)
                generated_text = (
                    "Here are the available commands:\n"
                    f"/ask — Ask {bot_display_name} about trending tokens, a ticker, or this community\n"
                    "/ca — Show this community's contract address\n"
                    "/setca — Admins: save this community's contract address\n"
                    "/price — Get live token price, market cap & liquidity\n"
                    "/links — Official website, Twitter, Telegram & TikTok\n"
                    "/help — Show all commands"
                )
                intent = "command_help"

            elif cmd == "setca":
                proj_title = get_project_name(norm_msg.project_id)
                if cmd_arg:
                    new_ca = cmd_arg.strip()
                    try:
                        from pathlib import Path
                        import yaml
                        cfg_file = Path(f"config/projects/{norm_msg.project_id}.yaml")
                        if cfg_file.exists():
                            raw = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
                            raw["token_address"] = new_ca
                            if "project" in raw and isinstance(raw["project"], dict):
                                raw["project"]["token_address"] = new_ca
                            cfg_file.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
                    except Exception as exc:
                        logger.warning("Could not persist setca to yaml: %s", exc)
                    generated_text = f"Official contract address for {proj_title} updated to:\n{new_ca}"
                else:
                    generated_text = f"Admins: to set or update this community's contract address, type:\n/setca <contract_address>"
                intent = "command_setca"

            elif cmd == "start":
                proj_title = get_project_name(norm_msg.project_id)
                bot_display_name = get_project_display_name(norm_msg.project_id)
                generated_text = (
                    f"Hey! I'm {bot_display_name}, the AI Community Manager for {proj_title}. "
                    f"Type /help to see all available commands, or just chat with me naturally!"
                )
                intent = "command_start"

            elif cmd == "ask":
                if cmd_arg:
                    import dataclasses
                    norm_msg = dataclasses.replace(norm_msg, text=cmd_arg)
                    intent = route_intent(cmd_arg)
                    logger.info("Command /ask stripped; routing query '%s' to intent '%s'", cmd_arg, intent)
                else:
                    generated_text = "What would you like to ask? Type /ask followed by your question, or just ask naturally!"
                    intent = "command_ask"

        if generated_text is not None:
            pass  # Intercepted and answered directly by slash command handler
        elif re.search(
            r"\b(?:group|community|chat|respond\s+to\s+them|what\s+did\s+they\s+ask|"
            r"respond\s+to\s+(?:the\s+)?(?:community|group|chat)|"
            r"reply\s+to\s+(?:the\s+)?(?:community|group|chat)|"
            r"answer\s+(?:the\s+)?(?:community|group|chat)|"
            r"what\s+(?:was|is)\s+(?:the\s+)?(?:question|last\s+question)\s+(?:in|from)\s+(?:the\s+)?(?:group|community|chat)|"
            r"check\s+(?:the\s+)?(?:group|community)\s*(?:logs|chat)?|"
            r"what\'?s\s+(?:happening|going\s+on)\s+in\s+(?:the\s+)?(?:group|community))\b",
            norm_msg.text,
            re.IGNORECASE,
        ):
            logger.info("Cross-chat awareness triggered for msg %d in project %s: '%s'", inbox_id, norm_msg.project_id, norm_msg.text)
            from zoe.memory.short_term import get_recent_group_messages
            target_grp = None
            try:
                from zoe.settings import load_project_config
                cfg_obj = load_project_config(norm_msg.project_id)
                target_grp = str(cfg_obj.get("telegram", {}).get("group_id") or "")
            except Exception:
                pass

            recent_grp_msgs = get_recent_group_messages(
                project_id=norm_msg.project_id,
                target_group_id=target_grp,
                limit=5,
                conn_op=conn_op,
                conn_mem=conn_mem,
            )

            if recent_grp_msgs:
                history_lines = []
                for m in recent_grp_msgs:
                    sender = "Zoe" if m.get("user_id") == "zoe" else "Community Member"
                    history_lines.append(f"{sender}: {m['text'].strip()}")
                recent_group_block = "\n".join(history_lines)
                logger.info("Retrieved %d recent group message(s) for cross-chat resolution", len(recent_grp_msgs))

                latest_user_text = next(
                    (m["text"] for m in reversed(recent_grp_msgs) if m.get("user_id") != "zoe"),
                    recent_grp_msgs[-1]["text"],
                )

                rag_start = time.perf_counter()
                official_chunks = search(
                    project_id=norm_msg.project_id,
                    query=latest_user_text,
                    top_k=2,
                    db_path=kb_db_path,
                    index_dir=index_dir,
                    model=model,
                )
                rag_time = round(time.perf_counter() - rag_start, 3)

                prompt = build_prompt(
                    message=norm_msg,
                    community_context=community_context,
                    official_chunks=official_chunks,
                    system_prompt=active_system_prompt,
                )
                prompt += (
                    f"\n\n[RECENT GROUP CHAT HISTORY]\n"
                    f"{recent_group_block}\n\n"
                    f"[JARVIS CROSS-CHAT DIRECTIVE]\n"
                    f"The user in this chat said: '{norm_msg.text}'. "
                    f"You have full access to database logs. Based on the [RECENT GROUP CHAT HISTORY] above, "
                    f"answer the user's question, summarize what the group discussed, or explain how you are responding to them based on official records. "
                    f"NEVER say 'I have a hard technical limitation', 'I cannot see the live feed', 'I cannot see the live group chat feed', or 'Please copy and paste'. "
                    f"Act with confident JARVIS competence."
                )

                client = llm_client or MockLLMClient()
                generated_text = _safe_generate(
                    client=client,
                    system_prompt=active_system_prompt,
                    user_prompt=prompt,
                    max_tokens=250,
                    project_id=norm_msg.project_id,
                )
            else:
                generated_text = "I just checked the group logs, but it's quiet right now."

        elif intent in ("crypto_intelligence", "ca_detection"):
            if not module_crypto_intel:
                logger.info("Crypto intelligence module disabled for project %s", norm_msg.project_id)
                generated_text = "I've detected a contract address, but the Crypto Intelligence module is currently disabled for this project."
            else:
                from zoe.conversation.router import extract_detected_ca
                from zoe.tools.crypto_intel import (
                    _DEFAULT_ANALYZE_SYNC,
                    analyze_contract_address_sync,
                    format_token_intel_response,
                    generate_ca_inline_keyboard,
                    get_token_intel_sync,
                )
                ca = detect_contract_address(norm_msg.text) or extract_detected_ca(norm_msg.text) or norm_msg.text.strip()
                logger.info("Executing on-demand Crypto Intelligence CA analysis for: %s", ca)
                if analyze_contract_address_sync is not _DEFAULT_ANALYZE_SYNC:
                    generated_text = analyze_contract_address_sync(ca)
                    inline_keyboard = generate_ca_inline_keyboard(ca)
                else:
                    intel = get_token_intel_sync(ca=ca, project_id=norm_msg.project_id)
                    generated_text = format_token_intel_response(intel)
                    inline_keyboard = generate_ca_inline_keyboard(ca, intel)
        elif intent == "general_knowledge":
            logger.info("Direct general knowledge / coding intent triggered for msg %d: '%s'", inbox_id, norm_msg.text)
            prompt = build_prompt(
                message=norm_msg,
                community_context=community_context,
                official_chunks=[],
                conversation_history=conversation_history,
                system_prompt=active_system_prompt,
            )
            client = llm_client or MockLLMClient()
            generated_text = _safe_generate(
                client=client,
                system_prompt=active_system_prompt,
                user_prompt=prompt,
                max_tokens=250,
                project_id=norm_msg.project_id,
            )
        elif intent == "proactive_fud":
            logger.info("Executing JARVIS proactive FUD intervention for inbox msg %d", inbox_id)
            official_chunks = search(
                project_id=norm_msg.project_id,
                query="liquidity contract security official status announcements tokenomics",
                top_k=3,
                db_path=kb_db_path,
                index_dir=index_dir,
                model=model,
            )
            token_addr = None
            try:
                from zoe.settings import load_project_config
                p_cfg = load_project_config(norm_msg.project_id)
                token_addr = p_cfg.get("token_address") or p_cfg.get("project", {}).get("token_address")
            except Exception:
                pass
            live_market_data = get_token_price_sync(token_addr or "") if token_addr else None

            prompt = build_proactive_prompt(
                community_context=community_context,
                official_chunks=official_chunks,
                live_market_data=live_market_data,
                system_prompt=active_system_prompt,
            )
            client = llm_client or MockLLMClient()
            generated_text = _safe_generate(
                client=client,
                system_prompt=active_system_prompt,
                user_prompt=prompt,
                max_tokens=150,
                project_id=norm_msg.project_id,
            )
        elif intent == "web_search":
            logger.info("Direct web search intent triggered for message %d: '%s'", inbox_id, norm_msg.text)
            token_query = extract_token_query(norm_msg.text)

            # Live global market data lookup for the specified token (CoinGecko / DexScreener)
            live_market_data = None
            if token_query and token_query.lower() not in {"the", "crypto", "market", "a", "an"}:
                try:
                    live_market_data = search_token_price_sync(token_query)
                except Exception as exc:
                    logger.warning("Token price search failed for '%s': %s", token_query, exc)

            # Fast short-circuit: If we have live authoritative market data, do not wait 3-4s for DuckDuckGo
            has_valid_price = bool(
                live_market_data
                and "Current Price:" in live_market_data
                and "Unable to" not in live_market_data
                and "No active trading pairs" not in live_market_data
            )

            if not has_valid_price or web_search_fn is not None:
                searcher = web_search_fn or search_web_sync
                try:
                    web_results = searcher(norm_msg.text) or []
                except Exception as exc:
                    logger.warning("Web search failed for query '%s': %s", norm_msg.text, exc)
                    web_results = []

            prompt = build_prompt(
                message=norm_msg,
                community_context=community_context,
                official_chunks=[],
                live_market_data=live_market_data,
                web_results=web_results,
                conversation_history=conversation_history,
                system_prompt=active_system_prompt,
            )
            client = llm_client or MockLLMClient()
            generated_text = _safe_generate(
                client=client,
                system_prompt=active_system_prompt,
                user_prompt=prompt,
                max_tokens=200,
                project_id=norm_msg.project_id,
            )
        elif intent == "api_call":
            token_addr = None
            try:
                from zoe.settings import load_project_config
                p_cfg = load_project_config(norm_msg.project_id)
                token_addr = p_cfg.get("token_address") or p_cfg.get("project", {}).get("token_address")
            except Exception:
                pass

            if not token_addr:
                try:
                    row_proj = conn_op.execute(
                        "SELECT config_json FROM projects WHERE project_id = ?",
                        (norm_msg.project_id,),
                    ).fetchone()
                    if row_proj and row_proj[0]:
                        p_cfg_db = json.loads(row_proj[0])
                        token_addr = p_cfg_db.get("token_address") or p_cfg_db.get("project", {}).get("token_address")
                except Exception:
                    pass

            from zoe.conversation.prompt_builder import get_project_display_name, get_project_name
            from zoe.tools.crypto_intel import format_token_intel_response, get_token_intel_sync

            def get_project_token_symbols(pid: str) -> List[str]:
                if pid == "onelove":
                    return ["onelove", "$onelove", "one love"]
                elif pid in ("live_test", "hummingbird"):
                    return ["fly", "$fly", "hummingbird", "$hb", "humminb"]
                try:
                    from zoe.settings import load_project_config
                    cfg = load_project_config(pid)
                    name = cfg.get("project", {}).get("name", "").lower()
                    sym = cfg.get("project", {}).get("symbol", "").lower()
                    return [s for s in (sym, f"${sym}", name) if s]
                except Exception:
                    return []

            native_tokens = get_project_token_symbols(norm_msg.project_id)
            default_sym = "ONELOVE" if norm_msg.project_id == "onelove" else ("FLY" if norm_msg.project_id in ("live_test", "hummingbird") else (native_tokens[0].upper().lstrip("$") if native_tokens else "TOKEN"))
            primary_symbol = f"${default_sym}"
            token_query = extract_token_query(norm_msg.text, default_token=default_sym)

            # Check if query targets a different project's token (Strict Tenant Isolation)
            if norm_msg.project_id == "onelove":
                is_cross_project = bool(re.search(r"\b(?:\$fly|fly|hummingbird|bitcoin|btc|ethereum|eth)\b", norm_msg.text, re.IGNORECASE))
            elif norm_msg.project_id in ("live_test", "hummingbird"):
                is_cross_project = bool(re.search(r"\b(?:\$onelove|onelove|one\s+love)\b", norm_msg.text, re.IGNORECASE))
            else:
                is_cross_project = False

            proj_title = get_project_name(norm_msg.project_id)

            if is_cross_project:
                # Intercept cross-project queries BEFORE calling DexScreener
                logger.info("[%s] Intercepted cross-project query '%s'; returning boundary refusal without DexScreener query.", norm_msg.project_id, norm_msg.text)
                generated_text = f"I only manage data for {proj_title}. I don't have specific info on that other token."
            else:
                from zoe.tools.crypto_intel import format_token_intel_response, generate_ca_inline_keyboard, get_token_intel_sync
                intel = get_token_intel_sync(token_address=token_addr, project_id=norm_msg.project_id)
                generated_text = format_token_intel_response(intel)
                if token_addr:
                    inline_keyboard = generate_ca_inline_keyboard(token_addr, intel, project_id=norm_msg.project_id)
        elif generated_text is None and (intent == "knowledge" or (intent != "general" and classification.category in ("direct_question", "project_discussion", "project_question"))):
            is_project_question = (intent == "knowledge" or classification.category in ("direct_question", "project_discussion", "project_question"))
            # Step 2: RAG Retrieval (top_k=3 for high-precision document recall)
            rag_start = time.perf_counter()
            official_chunks = search(
                project_id=norm_msg.project_id,
                query=norm_msg.text,
                top_k=3,
                db_path=kb_db_path,
                index_dir=index_dir,
                model=model,
            )
            rag_time = round(time.perf_counter() - rag_start, 3)

            rag_score = official_chunks[0].score if official_chunks else 0.0
            rag_failed = (not official_chunks) or (rag_score < 0.25)

            # Step 3: Web Search Fallback if RAG fails (score < 0.25)
            # Force Web Search OFF for Project Facts:
            # If the intent is a project_question / knowledge query, strictly use RAG.
            # Never search the web for project facts (founders, contract, tokenomics) to prevent
            # DuckDuckGo from returning unrelated tech billionaires or incorrect external entities.
            web_results: List[Dict[str, str]] = []
            if rag_failed and not enforce_accuracy_guard and not is_project_question:
                logger.info(
                    "RAG retrieval below threshold 0.25 (score=%.3f) for query: '%s'. Executing DuckDuckGo web search fallback.",
                    rag_score,
                    norm_msg.text,
                )
                searcher = web_search_fn or search_web_sync
                try:
                    web_results = searcher(norm_msg.text) or []
                except Exception as exc:
                    logger.warning("Web search fallback failed for '%s': %s", norm_msg.text, exc)
                    web_results = []
            elif rag_failed and is_project_question:
                logger.info(
                    "Project question RAG retrieval below threshold 0.25 (score=%.3f) for '%s'. Web search fallback forced OFF for project facts.",
                    rag_score,
                    norm_msg.text,
                )

            # Step 4: Generate response using LLM (injecting official docs or web results)
            use_guard = (
                enforce_accuracy_guard
                if enforce_accuracy_guard is not None
                else not isinstance(llm_client, MockLLMClient)
            )

            if rag_failed and not web_results:
                if use_guard or enforce_accuracy_guard:
                    logger.info(
                        "Accuracy Guard triggered: score below 0.25 and no web search results for query '%s'",
                        norm_msg.text,
                    )
                    generated_text = "I don't have the latest details on that yet. As soon as the team announces it, I'll have the update for you."
                else:
                    prompt = build_prompt(
                        message=norm_msg,
                        community_context=community_context,
                        official_chunks=[],
                        conversation_history=None if is_project_question else conversation_history,
                        system_prompt=active_system_prompt,
                    )
                    client = llm_client or MockLLMClient()
                    llm_start = time.perf_counter()
                    generated_text = _safe_generate(
                        client=client,
                        system_prompt=active_system_prompt,
                        user_prompt=prompt,
                        max_tokens=100,
                        project_id=norm_msg.project_id,
                    )
                    llm_time = round(time.perf_counter() - llm_start, 3)
            else:
                chunks_to_inject = official_chunks if not rag_failed else []
                # For factual project questions, strictly rely on [OFFICIAL KNOWLEDGE] and ignore short-term history to prevent device amnesia
                hist_for_prompt = None if is_project_question else conversation_history
                prompt = build_prompt(
                    message=norm_msg,
                    community_context=community_context,
                    official_chunks=chunks_to_inject,
                    web_results=web_results if rag_failed else None,
                    conversation_history=hist_for_prompt,
                    system_prompt=active_system_prompt,
                )
                client = llm_client or MockLLMClient()
                llm_start = time.perf_counter()
                generated_text = _safe_generate(
                    client=client,
                    system_prompt=active_system_prompt,
                    user_prompt=prompt,
                    max_tokens=100,
                    project_id=norm_msg.project_id,
                )
                llm_time = round(time.perf_counter() - llm_start, 3)
        elif generated_text is None:
            # Casual / general conversation without RAG constraint
            prompt = build_prompt(
                message=norm_msg,
                community_context=community_context,
                official_chunks=[],
                conversation_history=conversation_history,
                system_prompt=active_system_prompt,
            )
            client = llm_client or MockLLMClient()
            llm_start = time.perf_counter()
            generated_text = _safe_generate(
                client=client,
                system_prompt=active_system_prompt,
                user_prompt=prompt,
                max_tokens=100,
                project_id=norm_msg.project_id,
            )
            llm_time = round(time.perf_counter() - llm_start, 3)

        # Log pipeline latency profile
        logger.info(f"[{norm_msg.project_id}] Intent took: {intent_time}s")
        logger.info(f"[{norm_msg.project_id}] RAG took: {rag_time}s")
        logger.info(f"[{norm_msg.project_id}] LLM took: {llm_time}s")

        # Sanitize chat formatting: remove unnecessary characters, markdown artifacts, non-standard unicode
        if generated_text:
            generated_text = clean_unnecessary_characters(generated_text)
            if cmd not in ("help", "links", "socials", "social"):
                # Strict Leash: Never leak command menus in conversational responses
                generated_text = re.sub(
                    r"(?im)^\s*(?:[-•*]\s*)?/(?:ask|ca|setca|price|help|credits|add_credits|links|socials|social)\b.*$\n?",
                    "",
                    generated_text,
                )
                generated_text = re.sub(r"/(?:ca|setca|price|ask|help|credits|add_credits)\b", "", generated_text).strip()

        # Step 5: Validate safety (Fail-Closed)
        safety_config: Dict[str, Any] = {}
        try:
            from zoe.settings import load_project_config
            p_cfg_obj = load_project_config(norm_msg.project_id)
            if p_cfg_obj and "safety" in p_cfg_obj and "url_allowlist" in p_cfg_obj["safety"]:
                safety_config["url_allowlist"] = list(p_cfg_obj["safety"]["url_allowlist"])
        except Exception:
            pass
        if web_results:
            # Whitelist domains from web search results so citations remain safe
            try:
                from urllib.parse import urlparse
                search_domains = [
                    urlparse(r.get("href", "")).netloc.lower()
                    for r in web_results
                    if r.get("href")
                ]
                search_domains = [d for d in search_domains if d]
                if search_domains:
                    safety_config["approved_domains"] = search_domains
            except Exception:
                pass

        validator = safety_validator_fn or validate_output
        try:
            safety_res = validator(generated_text, official_chunks, config=safety_config)
        except Exception as exc:
            logger.error("Validator exception in pipeline (FAIL-CLOSED): %s", str(exc))
            safety_res = SafetyResult(
                is_safe=False,
                violations=[f"pipeline_validator_exception: {str(exc)}"],
                safe_text=None,
            )

        # 12. Enforce fail-closed safety check
        if not safety_res.is_safe:
            logger.warning(
                "Safety engine rejected generated text for inbox %s: %s",
                inbox_id,
                safety_res.violations,
            )
            # Abort safely without enqueuing unsafe response
            transition(conn_op, inbox_id, "no_response_required")
            conn_op.commit()
            return PipelineResult(
                inbox_id=inbox_id,
                responded=False,
                classification=classification,
                decision=decision,
                safety_result=safety_res,
                aborted=True,
            )

        # 13. Enqueue to outbox (simulated=True per Sink Mode)
        created_dt = now()
        created_str = format_timestamp(created_dt)
        retention_delete_str = format_timestamp(created_dt + timedelta(days=30))
        final_text = clean_unnecessary_characters(safety_res.safe_text or "")

        transition(conn_op, inbox_id, "response_pending")

        conn_op.execute(
            """
            INSERT INTO responses (
                project_id, group_id, trigger_message_id, text, safety_verdict, created_at, retention_delete_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                norm_msg.project_id,
                norm_msg.group_id,
                norm_msg.telegram_message_id,
                final_text,
                "safe",
                created_str,
                retention_delete_str,
            ),
        )

        # Determine simulated flag (0 if live send is enabled, 1 for sink mode)
        sim_val = 1
        if simulated is not None:
            sim_val = 1 if simulated else 0
        else:
            try:
                row_proj = conn_op.execute(
                    "SELECT config_json FROM projects WHERE project_id = ?",
                    (norm_msg.project_id,),
                ).fetchone()
                if row_proj and row_proj[0]:
                    p_cfg = json.loads(row_proj[0])
                    if p_cfg.get("telegram", {}).get("live_send_responses_enabled"):
                        sim_val = 0
            except Exception:
                sim_val = 1

        ik_json = json.dumps(inline_keyboard) if inline_keyboard else None
        outbox_cur = conn_op.execute(
            """
            INSERT INTO outbox_messages (
                project_id, inbox_message_id, group_id, reply_to_message_id, text,
                simulated, state, state_changed_at, created_at, inline_keyboard_json
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                norm_msg.project_id,
                inbox_id,
                norm_msg.group_id,
                norm_msg.telegram_message_id,
                final_text,
                sim_val,
                created_str,
                created_str,
                ik_json,
            ),
        )
        outbox_id = outbox_cur.lastrowid
        conn_op.commit()

        # Record Zoe's reply in community memory for short-term conversational context
        try:
            record_community_message(
                project_id=norm_msg.project_id,
                group_id=norm_msg.group_id,
                telegram_message_id=0,
                pseudonymous_user_id="zoe",
                content=final_text,
                received_at=created_dt,
                db_path=mem_db_path,
            )
        except Exception as exc:
            logger.warning("Failed to record Zoe response in community memory: %s", exc)

        return PipelineResult(
            inbox_id=inbox_id,
            responded=True,
            classification=classification,
            decision=decision,
            outbox_id=outbox_id,
            response_text=safety_res.safe_text,
            safety_result=safety_res,
            aborted=False,
            inline_keyboard=inline_keyboard,
        )

    finally:
        if close_conns:
            conn_op.close()
            conn_kb.close()
            conn_mem.close()


def trigger_proactive_intervention(
    project_id: str,
    group_id: str,
    db_conns: Optional[Dict[str, sqlite3.Connection]] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    kb_db_path: Optional[Union[str, Path]] = None,
    mem_db_path: Optional[Union[str, Path]] = None,
    index_dir: Optional[Union[str, Path]] = None,
    llm_client: Optional[Any] = None,
    model: Optional[Any] = None,
    simulated: Optional[bool] = None,
    force: bool = False,
) -> Optional[int]:
    """Autonomous proactive sentiment monitor intervention (JARVIS Mode).

    Checks recent community messages for 'panicked/fud' sentiment.
    If detected, retrieves RAG documents and market data, generates a JARVIS intervention,
    and enqueues it to outbox_messages without requiring a user prompt.
    Returns outbox_id if triggered, None otherwise.
    """
    conns = db_conns or {}
    conn_op = conns.get("operational") or open_operational_db(
        op_db_path or "data/operational/operational.db"
    )
    conn_kb = conns.get("knowledge") or open_official_knowledge_db(
        kb_db_path or "data/official_knowledge/official_knowledge.db"
    )
    conn_mem = conns.get("memory") or open_community_memory_db(
        mem_db_path or "data/community_memory/community_memory.db"
    )
    close_conns = db_conns is None

    try:
        recent_context = get_recent_context(
            project_id=project_id,
            group_id=group_id,
            limit=15,
            db_path=mem_db_path,
        )

        sentiment = analyze_group_sentiment_sync(recent_context, llm_client=llm_client)
        if sentiment != "panicked/fud" and not force:
            logger.debug("Proactive sentiment check: group %s sentiment is '%s'; no intervention required.", group_id, sentiment)
            return None

        # Check 10-minute cooldown (600 seconds) unless force=True
        if not force:
            cur_cd = conn_op.execute(
                """
                SELECT MAX(created_at) FROM inbox_messages
                WHERE project_id = ? AND group_id = ? AND decision_reason = 'proactive_fud_intervention'
                """,
                (project_id, group_id),
            )
            row_cd = cur_cd.fetchone()
            if row_cd and row_cd[0]:
                try:
                    from zoe.clock.clock import parse_timestamp
                    last_fud_dt = parse_timestamp(row_cd[0])
                    elapsed = (now() - last_fud_dt).total_seconds()
                    if elapsed < 600.0:
                        logger.info("Proactive intervention suppressed: 10-minute cooldown active (elapsed=%.1fs < 600s)", elapsed)
                        return None
                except Exception:
                    pass

        logger.info("Proactive Sentiment Radar triggered for group %s: sentiment='%s'. Generating JARVIS response.", group_id, sentiment)

        official_chunks = search(
            project_id=project_id,
            query="liquidity contract security official status announcements tokenomics",
            top_k=3,
            db_path=kb_db_path,
            index_dir=index_dir,
            model=model,
        )

        token_addr = None
        try:
            from zoe.settings import load_project_config
            p_cfg = load_project_config(project_id)
            token_addr = p_cfg.get("token_address") or p_cfg.get("project", {}).get("token_address")
        except Exception:
            pass

        live_market_data = get_token_price_sync(token_addr or "") if token_addr else None

        prompt = build_proactive_prompt(
            community_context=recent_context,
            official_chunks=official_chunks,
            live_market_data=live_market_data,
        )

        client = llm_client or MockLLMClient()
        generated_text = _safe_generate(
            client=client,
            system_prompt=DEFAULT_ZOE_IDENTITY_PROMPT,
            user_prompt=prompt,
            max_tokens=250,
        )

        if generated_text:
            generated_text = clean_unnecessary_characters(generated_text)

        validator = validate_output
        safety_res = validator(generated_text, official_chunks)
        if not safety_res.is_safe:
            logger.warning("Proactive response rejected by safety engine: %s", safety_res.violations)
            return None

        final_text = clean_unnecessary_characters(safety_res.safe_text or "")
        now_dt = now()
        now_str = format_timestamp(now_dt)
        retention_delete_str = format_timestamp(now_dt + timedelta(days=30))

        # Create system radar inbox record for audit compliance and foreign keys
        cur_inbox = conn_op.execute(
            """
            INSERT INTO inbox_messages (
                project_id, telegram_update_id, group_id, telegram_message_id,
                pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at,
                classification_category, classification_confidence, decision, decision_reason
            ) VALUES (?, 0, ?, 0, 'system_radar', '[PROACTIVE_SENTIMENT_RADAR]', ?, 'response_pending', ?, ?, 'escalation_trigger', 1.0, 'respond', 'proactive_fud_intervention')
            """,
            (project_id, group_id, now_str, now_str, now_str),
        )
        inbox_id = cur_inbox.lastrowid

        # Record in responses table
        conn_op.execute(
            """
            INSERT INTO responses (
                project_id, group_id, trigger_message_id, text, safety_verdict, created_at, retention_delete_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, group_id, 0, final_text, "safe", now_str, retention_delete_str),
        )

        sim_val = 1
        if simulated is not None:
            sim_val = 1 if simulated else 0
        else:
            try:
                row_proj = conn_op.execute(
                    "SELECT config_json FROM projects WHERE project_id = ?",
                    (project_id,),
                ).fetchone()
                if row_proj and row_proj[0]:
                    p_cfg = json.loads(row_proj[0])
                    if p_cfg.get("telegram", {}).get("live_send_responses_enabled"):
                        sim_val = 0
            except Exception:
                sim_val = 1

        outbox_cur = conn_op.execute(
            """
            INSERT INTO outbox_messages (
                project_id, inbox_message_id, group_id, reply_to_message_id, text,
                simulated, state, state_changed_at, created_at
            ) VALUES (?, ?, ?, NULL, ?, ?, 'pending', ?, ?)
            """,
            (project_id, inbox_id, group_id, final_text, sim_val, now_str, now_str),
        )
        outbox_id = outbox_cur.lastrowid
        conn_op.commit()

        try:
            record_community_message(
                project_id=project_id,
                group_id=group_id,
                telegram_message_id=0,
                pseudonymous_user_id="zoe",
                content=final_text,
                received_at=now_dt,
                db_path=mem_db_path,
            )
        except Exception as exc:
            logger.warning("Failed to record proactive response in community memory: %s", exc)

        logger.info("Proactive JARVIS message enqueued to outbox msg %d for group %s", outbox_id, group_id)
        return outbox_id

    finally:
        if close_conns:
            conn_op.close()
            conn_kb.close()
            conn_mem.close()


