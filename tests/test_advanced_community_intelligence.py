"""Test Suite for Advanced Community & Wallet Intelligence (Coral Feature Parity).

Tests:
1. X / Twitter Account Scorer & Trust Meter (src/zoe/tools/x_scraper.py)
2. Wallet PnL, Holdings & Net Worth Flex Curve (src/zoe/tools/wallet_intel.py)
3. Formal Token Calls & Conviction 1-5 Weighting (src/zoe/tools/caller_reputation.py)
4. Community Games (/play) & Prediction Markets (/pm) (src/zoe/tools/games.py)
5. Pipeline Telegram Command Routing (src/zoe/worker/pipeline.py)
"""

import asyncio
from datetime import datetime, timezone
import pytest
import uuid

from zoe.tools.x_scraper import (
    analyze_x_account,
    analyze_x_account_sync,
    format_x_intel_card,
    _calculate_trust_score,
)
from zoe.tools.wallet_intel import (
    get_wallet_pnl,
    get_wallet_flex,
    format_pnl_card,
    format_flex_card,
    _get_whale_tier,
    _generate_sparkline,
)
from zoe.tools.caller_reputation import (
    record_token_call,
    get_community_leaderboard_data,
    get_leaderboard_text,
)
from zoe.tools.games import (
    create_prediction,
    vote_prediction,
    get_active_predictions,
    generate_play_challenge,
    format_prediction_card,
)


def test_x_scorer_algorithm():
    """Test trust score calculation and tiering logic."""
    # Elite account
    score_elite = _calculate_trust_score(
        followers=150_000,
        following=350,
        age_days=2500,
        verified=True,
        statuses_count=10_000,
    )
    assert score_elite["trust_score"] >= 80
    assert score_elite["risk_level"] == "LOW"

    # Fresh bot account
    score_bot = _calculate_trust_score(
        followers=5,
        following=450,
        age_days=3,
        verified=False,
        statuses_count=0,
    )
    assert score_bot["trust_score"] <= 35
    assert score_bot["risk_level"] in ("HIGH", "CRITICAL")


def test_x_scorer_analysis_and_card():
    """Test full X account analysis and markdown card generation."""
    res = asyncio.run(analyze_x_account("elonmusk"))
    assert "username" in res
    assert res["username"] == "elonmusk"
    assert res["trust_score"] > 0
    assert "risk_level" in res

    card = format_x_intel_card(res)
    assert "X/Twitter Intelligence Analysis" in card
    assert "Trust Score" in card
    assert "Followers" in card


def test_wallet_intel_pnl_and_flex():
    """Test Solana wallet PnL and flex curve valuation."""
    test_wallet = "F1r5AqRj8bJyzM4nU2pV8H1JQT8ToR4rvjj2YwxHmoon"
    pnl = asyncio.run(get_wallet_pnl(test_wallet))
    assert "wallet" in pnl
    assert pnl["wallet"] == test_wallet
    assert "net_worth_usd" in pnl
    assert "tier_name" in pnl
    assert pnl["net_worth_usd"] > 0

    flex = asyncio.run(get_wallet_flex(test_wallet))
    assert "allocations" in flex
    assert "sparkline" in flex

    pnl_card = format_pnl_card(pnl)
    assert "Wallet PnL Performance Audit" in pnl_card
    assert "Realized PnL" in pnl_card

    flex_card = format_flex_card(flex)
    assert "ON-CHAIN WALLET FLEX" in flex_card
    assert "Top Holdings" in flex_card


def test_whale_tiers_and_sparklines():
    """Test whale tier badges and ASCII curve generation."""
    tier_shrimp, _ = _get_whale_tier(500.0)
    assert "Shrimp" in tier_shrimp

    tier_whale, _ = _get_whale_tier(250_000.0)
    assert "Whale" in tier_whale

    curve = _generate_sparkline([10.0, 15.0, 12.0, 25.0, 40.0])
    assert len(curve) == 5


def test_formal_calls_and_conviction_reputation():
    """Test recording a token call with conviction and weighted leaderboard calculation."""
    proj_id = f"test_proj_{uuid.uuid4().hex[:6]}"
    user_id = f"test_user_{uuid.uuid4().hex[:6]}"
    ca = "F1r5AqRj8bJyzM4nU2pV8H1JQT8ToR4rvjj2YwxHmoon"

    # Call with conviction 5
    call_res = record_token_call(
        project_id=proj_id,
        telegram_user_id=user_id,
        contract_address=ca,
        username="AlphaChad",
        call_price=0.015,
        conviction=5,
    )
    assert call_res is not None
    assert call_res["conviction"] == 5

    # Retrieve leaderboard
    lb_data = get_community_leaderboard_data(proj_id)
    assert len(lb_data) > 0
    top = lb_data[0]
    assert top["username"] == "@AlphaChad"
    assert top["avg_conviction"] == 5.0
    assert top["conviction_score"] >= 1.0

    lb_text = get_leaderboard_text(proj_id)
    assert "Top Callers Leaderboard" in lb_text
    assert "AlphaChad" in lb_text


def test_games_and_prediction_markets():
    """Test /play trivia challenge and /pm prediction market creation and voting."""
    # 1. Play challenge
    play = generate_play_challenge()
    assert "game_id" in play
    assert "reply_markup" in play
    assert len(play["reply_markup"]["inline_keyboard"]) >= 3

    # 2. Prediction market
    proj_id = f"test_proj_{uuid.uuid4().hex[:6]}"
    pred = create_prediction(
        project_id=proj_id,
        question="Will $FLY hit $1.00 by Friday?",
        creator_id="admin_123",
        target_value=1.00,
        duration_hours=24,
    )
    assert pred["id"] is not None
    assert pred["status"] == "active"

    # Vote YES
    v_res = vote_prediction(pred["id"], user_id="voter_1", choice="yes")
    assert v_res["success"] is True
    assert v_res["yes_votes"] == 1

    # Vote NO from another user
    v_res2 = vote_prediction(pred["id"], user_id="voter_2", choice="no")
    assert v_res2["success"] is True
    assert v_res2["no_votes"] == 1

    # Prevent double voting
    v_dup = vote_prediction(pred["id"], user_id="voter_1", choice="yes")
    assert "error" in v_dup

    # Active predictions list
    active = get_active_predictions(proj_id)
    assert len(active) >= 1
    assert active[0]["total_votes"] == 2

    # Card formatting
    card_text, markup = format_prediction_card(active[0])
    assert "Zoe Community Prediction Market" in card_text
    assert "Will $FLY hit $1.00 by Friday?" in card_text
    assert len(markup["inline_keyboard"][0]) == 2
