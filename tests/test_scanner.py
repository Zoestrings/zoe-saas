"""Unit and integration tests for Zoe Intelligence Scanner (Milestone 1: Solana Contract Intelligence)."""

import pytest
from zoe.tools.scanner import (
    evaluate_risk,
    format_scan_report,
    generate_scanner_inline_keyboard,
    investigate_project_osint,
    is_valid_solana_ca,
    scan_solana_token,
    scan_solana_token_sync,
    shorten_ca,
)


def test_is_valid_solana_ca():
    """Test Solana CA format validation."""
    # Valid Base58 Solana public keys (32-44 characters)
    assert is_valid_solana_ca("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263") is True
    assert is_valid_solana_ca("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") is True
    assert is_valid_solana_ca("So11111111111111111111111111111111111111112") is True

    # Invalid formats
    assert is_valid_solana_ca("") is False
    assert is_valid_solana_ca("   ") is False
    assert is_valid_solana_ca("invalid_ca") is False
    assert is_valid_solana_ca("0x1234567890abcdef1234567890abcdef12345678") is False  # EVM address
    assert is_valid_solana_ca("00000000000000000000000000000000") is False  # Contains '0' (not in base58)
    assert is_valid_solana_ca("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII") is False  # Contains 'I' (not in base58)


def test_shorten_ca():
    """Test CA abbreviation."""
    ca = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    assert shorten_ca(ca) == "DezX...B263"
    assert shorten_ca("short") == "short"


def test_evaluate_risk_deterministic():
    """Test deterministic risk evaluation logic for Mega-Module 1."""
    # 1. Safe Token (Mint revoked, Freeze revoked, distributed holders, LP locked, dev <= 5%, strong liquidity)
    safe_market = {
        "found": True,
        "price_usd": 0.000025,
        "market_cap": 250_000_000,
        "liquidity_usd": 150_000,
    }
    safe_security = {
        "success": True,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": 35.5,
        "is_honeypot": False,
        "lp_locked": True,
        "lp_lock_percent": 100.0,
        "dev_wallet_percent": 0.0,
    }
    risk_safe = evaluate_risk(safe_market, safe_security)
    assert risk_safe["level"] == "LOW"
    assert any("revoked" in r.lower() for r in risk_safe["reasons"])
    assert any("locked" in r.lower() for r in risk_safe["reasons"])

    # 2. Critical Risk: Top 10 Holders > 80%
    critical_conc_sec = {
        "success": True,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": 88.5,
        "is_honeypot": False,
        "lp_locked": True,
        "lp_lock_percent": 100.0,
        "dev_wallet_percent": 2.0,
    }
    risk_conc = evaluate_risk(safe_market, critical_conc_sec)
    assert risk_conc["level"] == "CRITICAL"
    assert any("holder concentration" in r.lower() for r in risk_conc["reasons"])

    # 3. High Risk: Dev Wallet > 10%
    high_dev_sec = {
        "success": True,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": 30.0,
        "is_honeypot": False,
        "lp_locked": True,
        "lp_lock_percent": 100.0,
        "dev_wallet_percent": 18.5,
    }
    risk_dev = evaluate_risk(safe_market, high_dev_sec)
    assert risk_dev["level"] == "HIGH"
    assert any("developer wallet holds" in r.lower() for r in risk_dev["reasons"])

    # 4. High Risk: Liquidity NOT Locked / Renounced
    unlocked_lp_sec = {
        "success": True,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": 30.0,
        "is_honeypot": False,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "dev_wallet_percent": 1.0,
    }
    risk_unlocked = evaluate_risk(safe_market, unlocked_lp_sec)
    assert risk_unlocked["level"] == "HIGH"
    assert any("liquidity is not locked" in r.lower() for r in risk_unlocked["reasons"])

    # 5. High Risk: Mint Authority is Active
    active_mint_sec = {
        "success": True,
        "mint_revoked": False,  # Active
        "freeze_revoked": True,
        "top_10_holders_percent": 30.0,
        "is_honeypot": False,
        "lp_locked": True,
        "lp_lock_percent": 100.0,
        "dev_wallet_percent": 0.0,
    }
    risk_mint = evaluate_risk(safe_market, active_mint_sec)
    assert risk_mint["level"] in ("HIGH", "CRITICAL")
    assert any("Mint Authority is active" in r for r in risk_mint["reasons"])

    # 6. High Risk: Liquidity < $5,000
    low_liq_market = {
        "found": True,
        "price_usd": 0.001,
        "market_cap": 100_000,
        "liquidity_usd": 2_500,  # Under $5,000
    }
    risk_liq = evaluate_risk(low_liq_market, safe_security)
    assert risk_liq["level"] in ("HIGH", "CRITICAL")
    assert any("Low liquidity" in r for r in risk_liq["reasons"])

    # 7. Critical Risk: Honeypot / Transfer Block
    honeypot_sec = {
        "success": True,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": 30.0,
        "is_honeypot": True,
        "lp_locked": True,
        "lp_lock_percent": 100.0,
        "dev_wallet_percent": 0.0,
    }
    risk_hp = evaluate_risk(safe_market, honeypot_sec)
    assert risk_hp["level"] == "CRITICAL"
    assert any("Honeypot" in r for r in risk_hp["reasons"])

    # 8. Medium Risk: No Official Website Found (Mega-Module 2)
    no_web_osint = {
        "has_official_website": False,
        "website": None,
        "is_anonymous_founder": False,
        "founder": "Public Founder",
    }
    risk_noweb = evaluate_risk(safe_market, safe_security, osint=no_web_osint)
    assert risk_noweb["level"] in ("MEDIUM", "HIGH", "CRITICAL")
    assert any("no official website" in r.lower() for r in risk_noweb["reasons"])

    # 9. Informational Flag: Anonymous / Unverified Founder
    anon_osint = {
        "has_official_website": True,
        "website": "https://bonkcoin.com",
        "is_anonymous_founder": True,
        "founder": "Anonymous / Unverified",
    }
    risk_anon = evaluate_risk(safe_market, safe_security, osint=anon_osint)
    assert any("founder identity is unverified" in r.lower() for r in risk_anon["reasons"])


def test_invalid_ca_scan():
    """Test scanner behavior with invalid CA."""
    res = scan_solana_token_sync("not_a_valid_solana_ca")
    assert res["valid"] is False
    assert "Invalid contract address format" in res["error"]

    report = format_scan_report(res)
    assert "Investigation Error" in report or "Invalid" in report


def test_format_scan_report_structure():
    """Verify that format_scan_report conforms to the exact required schema."""
    mock_data = {
        "valid": True,
        "ca": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "ca_short": "DezX...B263",
        "name": "Bonk",
        "symbol": "BONK",
        "market": {
            "found": True,
            "price_usd": 0.0000215,
            "market_cap": 1_850_000_000,
            "liquidity_usd": 220_000,
            "pair_url": "https://dexscreener.com/solana/5zpyutju9ee6jfymdgok7f6s5kczqtc9fomp3uekuya9",
        },
        "security": {
            "success": True,
            "mint_revoked": True,
            "freeze_revoked": True,
            "top_10_holders_percent": 41.2,
        },
        "risk": {
            "level": "LOW",
            "reasons": [
                "Mint Authority is revoked (fixed supply)",
                "Freeze Authority is revoked (accounts cannot be frozen)",
                "Healthy holder distribution: Top 10 hold 41.2%",
            ],
        },
        "project_osint": {
            "has_official_website": True,
            "website": "https://www.bonkcoin.com",
            "twitter": "https://twitter.com/bonk_inu",
            "founder": "Nom",
            "is_anonymous_founder": False,
        },
        "timestamp_utc": "2026-11-16 12:00:00 UTC",
    }

    report = format_scan_report(mock_data)

    # Check required headings and elements
    assert "🔍 Zoe Intelligence Report" in report
    assert "**Bonk** (CA: DezX...B263) · Solana" in report
    assert "🚨 Risk Assessment: LOW" in report
    assert "- Mint Authority is revoked (fixed supply)" in report
    assert "📊 Market Data" in report
    assert "Price: $" in report
    assert "Market Cap: $" in report
    assert "Liquidity: $" in report
    assert "🛡️ Security & Holder Intelligence" in report
    assert "Mint Auth: Revoked" in report
    assert "Freeze Auth: Revoked" in report
    assert "🌐 Project Info" in report
    assert "Website: https://www.bonkcoin.com" in report
    assert "Twitter: https://twitter.com/bonk_inu" in report
    assert "Founder: Nom" in report
    assert "Evidence Sources: DexScreener, GoPlus" in report
    assert "(This is a preliminary scan, not financial advice.)" in report


def test_investigate_project_osint():
    """Test OSINT extraction function."""
    import asyncio
    res = asyncio.run(investigate_project_osint(token_name="Bonk", symbol="BONK"))
    assert isinstance(res, dict)
    assert "founder" in res
    assert "is_anonymous_founder" in res
    assert "has_official_website" in res
    assert "website" in res


def test_generate_scanner_inline_keyboard():
    """Test inline buttons generation for DexScreener chart and Explorer."""
    ca = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    kb = generate_scanner_inline_keyboard(ca)
    assert len(kb) == 1
    assert len(kb[0]) == 2
    assert kb[0][0]["text"] == "📊 Live Chart"
    assert "dexscreener.com" in kb[0][0]["url"]
    assert "Explorer" in kb[0][1]["text"]
    assert f"solscan.io/token/{ca}" in kb[0][1]["url"]


def test_live_scan_solana_token():
    """Live integration test against DexScreener & GoPlus for BONK token."""
    import asyncio
    bonk_ca = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    res = asyncio.run(scan_solana_token(bonk_ca))

    assert res["valid"] is True
    assert res["risk"]["level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN")
    if res.get("market", {}).get("found"):
        assert "bonk" in res["name"].lower()
        assert "bonk" in res["symbol"].lower()
        assert res["market"]["price_usd"] is not None
        assert res["market"]["liquidity_usd"] is not None

    # Test report formatting on live data
    report = format_scan_report(res)
    assert "🔍 Zoe Intelligence Report" in report
    assert "Evidence Sources" in report


def test_pipeline_investigate_command_interception(tmp_path):
    """Test that /investigate commands in pipeline bypass LLM and return scanner reports."""
    from zoe.db.connections import open_operational_db, open_official_knowledge_db, open_community_memory_db
    from zoe.worker.pipeline import process_message

    op_db = tmp_path / "op.db"
    kb_db = tmp_path / "kb.db"
    mem_db = tmp_path / "mem.db"

    conn_op = open_operational_db(op_db)
    conn_kb = open_official_knowledge_db(kb_db)
    conn_mem = open_community_memory_db(mem_db)

    conn_op.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('onelove', 'One Love AI', '-5214407126', '{}', '2026-11-16T12:00:00Z', 1)
        """
    )
    conn_op.commit()

    def insert_inbox_msg(msg_id, text):
        conn_op.execute(
            """
            INSERT INTO inbox_messages (
                id, project_id, telegram_update_id, group_id, telegram_message_id,
                pseudonymous_user_id, text, state, state_changed_at, message_timestamp, created_at
            ) VALUES (?, 'onelove', ?, '-5214407126', ?, 'anon_user', ?, 'message_persisted', '2026-11-16T12:00:00Z', '2026-11-16T12:00:00Z', '2026-11-16T12:00:00Z')
            """,
            (msg_id, 100 + msg_id, 200 + msg_id, text),
        )
        conn_op.commit()

    # 1. Test /investigate without CA
    insert_inbox_msg(1, "/investigate")
    inbox_row_missing = {
        "id": 1,
        "project_id": "onelove",
        "telegram_update_id": 101,
        "group_id": -5214407126,
        "telegram_message_id": 201,
        "pseudonymous_user_id": "anon_user_1",
        "text": "/investigate",
        "message_timestamp": "2026-11-16T12:00:00Z",
        "state": "message_persisted",
    }

    res_missing = process_message(
        inbox_row=inbox_row_missing,
        db_conns={"operational": conn_op, "knowledge": conn_kb, "community_memory": conn_mem},
        simulated=True,
    )
    assert res_missing.responded is True
    assert "Please provide a Solana contract address" in res_missing.response_text

    # 2. Test /investigate with invalid CA
    insert_inbox_msg(2, "/investigate not_a_valid_solana_key")
    inbox_row_invalid = {
        "id": 2,
        "project_id": "onelove",
        "telegram_update_id": 102,
        "group_id": -5214407126,
        "telegram_message_id": 202,
        "pseudonymous_user_id": "anon_user_2",
        "text": "/investigate not_a_valid_solana_key",
        "message_timestamp": "2026-11-16T12:01:00Z",
        "state": "message_persisted",
    }

    res_invalid = process_message(
        inbox_row=inbox_row_invalid,
        db_conns={"operational": conn_op, "knowledge": conn_kb, "community_memory": conn_mem},
        simulated=True,
    )
    assert res_invalid.responded is True
    assert "Invalid Solana Address" in res_invalid.response_text

    # 3. Test /investigate with valid CA (BONK)
    bonk_ca = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    insert_inbox_msg(3, f"/investigate {bonk_ca}")
    inbox_row_valid = {
        "id": 3,
        "project_id": "onelove",
        "telegram_update_id": 103,
        "group_id": -5214407126,
        "telegram_message_id": 203,
        "pseudonymous_user_id": "anon_user_3",
        "text": f"/investigate {bonk_ca}",
        "message_timestamp": "2026-11-16T12:02:00Z",
        "state": "message_persisted",
    }

    res_valid = process_message(
        inbox_row=inbox_row_valid,
        db_conns={"operational": conn_op, "knowledge": conn_kb, "community_memory": conn_mem},
        simulated=True,
    )
    assert res_valid.responded is True
    assert "🔍 Zoe Intelligence Report" in res_valid.response_text
    assert "🚨 Risk Assessment:" in res_valid.response_text
    assert "📊 Market Data" in res_valid.response_text
    assert "🛡️ Security & Holder Intelligence" in res_valid.response_text
    assert res_valid.inline_keyboard is not None
    assert any("Live Chart" in btn["text"] for row in res_valid.inline_keyboard for btn in row)
    assert any("Explorer" in btn["text"] for row in res_valid.inline_keyboard for btn in row)

