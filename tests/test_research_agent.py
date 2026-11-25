"""Tests for the Autonomous Scheduled Research Reporter (Pillar 3)."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from zoe.agents.research_agent import generate_daily_report


def test_generate_daily_report_persists_3_paragraph_brief(tmp_path: Path, monkeypatch):
    """Verify generate_daily_report fetches market, news, X intel and persists a 3-paragraph brief."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    with (
        patch("zoe.agents.research_agent.get_token_price", new=AsyncMock(return_value="Price: $0.042 | Liquidity: $185,000 | 24h: +8.5%")),
        patch("zoe.agents.research_agent.search_token_price", new=AsyncMock(return_value="Price: $0.042 | Liquidity: $185,000 | 24h: +8.5%")),
        patch("zoe.agents.research_agent.search_web", new=AsyncMock(return_value=[
            {"title": "One Love AI expands Solana integration", "snippet": "New ecosystem partnership announced.", "url": "https://cointelegraph.com/example"}
        ])),
        patch("zoe.agents.research_agent.analyze_x_sentiment", new=AsyncMock(return_value={
            "sentiment": "Bullish",
            "summary": "Community is excited about upcoming staking milestones.",
            "bearish_factors": ["Low weekend volume"],
        })),
    ):
        report = asyncio.run(
            generate_daily_report(
                project_id="proj_test_001",
                project_name="One Love AI",
                token_address="So11111111111111111111111111111111111111112",
            )
        )

    assert report["project_id"] == "proj_test_001"
    assert report["id"]
    assert report["created_at"]
    assert "One Love AI" in report["report_text"]
    assert "Bullish" in report["report_text"]
    # Verify 3-paragraph structure
    paragraphs = [p.strip() for p in report["report_text"].split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
