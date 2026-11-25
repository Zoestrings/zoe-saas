"""Comprehensive automated test suite for Phase 3: Advanced Scanner, Narrative Detection & Social Intelligence."""

import pytest
from zoe.scanner.models import AlertSeverity, SentimentClass
from zoe.scanner.narratives import NarrativeDetectionEngine, FOUNDATIONAL_NARRATIVES
from zoe.scanner.sentiment import SentimentIntelligenceEngine
from zoe.scanner.mindshare import MindshareEngine
from zoe.scanner.momentum import MomentumEngine
from zoe.scanner.social import SocialIntelligenceEngine
from zoe.scanner.trending import TrendingDiscoveryEngine
from zoe.scanner.alerts import ScannerAlertEngine, ScannerAlertRule
from zoe.scanner.reports import IntelligenceReportGenerator


def test_narrative_detection_clustering():
    """Verify narrative clustering and keyword extraction across documents."""
    engine = NarrativeDetectionEngine()

    sample_docs = [
        {"title": "Virtuals Protocol launches autonomous agent framework", "snippet": "New AI swarms on-chain.", "sentiment_score": 0.6},
        {"title": "Helium expands DePIN wireless mesh compute", "snippet": "Decentralized hardware nodes grow 30%.", "sentiment_score": 0.4},
        {"title": "BlackRock expands tokenized Treasuries in RWA push", "snippet": "Institutional yield on-chain.", "sentiment_score": 0.5},
        {"title": "Autonomous agent swarms coordinate on ElizaOS", "snippet": "Decentralized AI bots.", "sentiment_score": 0.8},
    ]

    records = engine.extract_narratives_from_corpus(sample_docs)
    assert len(records) > 0

    # AI agents should be detected with high frequency
    ai_record = next((r for r in records if r.id == "ai_agents"), None)
    assert ai_record is not None
    assert ai_record.current_frequency >= 2
    assert "Autonomous AI Agents" in ai_record.name
    assert ai_record.mindshare_pct > 0.0


def test_sentiment_classification_and_sarcasm():
    """Verify sentiment engine properly detects positive, negative, and sarcastic crypto language."""
    engine = SentimentIntelligenceEngine()

    # Positive sample
    pos_res = engine.classify_text_sentiment("Massive bullish partnership announced, mainnet is live and audited safu!")
    assert pos_res[0] == SentimentClass.POSITIVE
    assert pos_res[1] > 0.2

    # Negative sample
    neg_res = engine.classify_text_sentiment("Warning: honeypot exploit detected! Dev dumped all liquidity and rugged the community.")
    assert neg_res[0] == SentimentClass.NEGATIVE
    assert neg_res[1] < -0.2

    # Sarcastic sample (inverted to negative)
    sarcastic_res = engine.classify_text_sentiment("Yeah right, surely nothing bad will happen, totally legit token to the moon 📉")
    assert sarcastic_res[2] is True  # Sarcasm detected
    assert sarcastic_res[0] == SentimentClass.NEGATIVE


def test_sentiment_spam_and_coordinated_activity_detection():
    """Verify spam filtering and astroturfing/coordinated activity flags."""
    engine = SentimentIntelligenceEngine()

    spam_posts = [
        {"text": "AIRDROP CLAIM FREE MINT connect wallet now to claim your $1000", "author": "bot_1"},
        {"text": "$BTC $ETH $SOL $PEPE $BONK $DOGE $SHIB $WIF buy now", "author": "bot_2"},
        {"text": "Legitimate discussion about Solana decentralization.", "author": "real_user_1"},
    ]

    clean_posts, spam_count, dup_count = engine.filter_and_deduplicate(spam_posts)
    assert spam_count == 2
    assert len(clean_posts) == 1

    # Coordinated activity test: 10 posts from only 2 authors
    astro_posts = [
        {"text": f"Token XYZ is the best coin ever iteration {i}", "author": "shill_account_1" if i % 2 == 0 else "shill_account_2"}
        for i in range(10)
    ]
    res = engine.analyze_corpus_sentiment("XYZ", astro_posts)
    assert res.coordinated_activity_flag is True
    assert "Coordinated activity detected" in res.context_notes


def test_mindshare_mathematical_calculation():
    """Verify mindshare formula computes authentic percentages weighted by author diversity."""
    sample_projects = [
        {"name": "AlphaBot", "symbol": "ABOT", "posts_count": 100, "unique_authors": 80, "previous_mindshare_pct": 50.0},
        {"name": "SpamToken", "symbol": "SPAM", "posts_count": 100, "unique_authors": 5, "previous_mindshare_pct": 20.0},
    ]

    res = MindshareEngine.calculate_project_mindshare("AI Agents", sample_projects, timeframe="24h")
    assert len(res.projects) == 2

    # AlphaBot should have significantly higher mindshare because of 80 unique authors vs SpamToken's 5
    alpha = next(p for p in res.projects if p["name"] == "AlphaBot")
    spam = next(p for p in res.projects if p["name"] == "SpamToken")

    assert alpha["mindshare_pct"] > spam["mindshare_pct"]
    assert alpha["author_diversity_ratio"] == 0.8
    assert spam["author_diversity_ratio"] == 0.05
    assert "Calculated as" in res.methodology


def test_momentum_velocity_and_anomaly_flags():
    """Verify momentum velocity, acceleration status, and anomaly detection."""
    # Surging anomaly: current volume 200 vs baseline 20 (900% growth)
    surging_res = MomentumEngine.calculate_momentum(
        entity_name="Virtuals Protocol",
        entity_type="project",
        current_24h_volume=200,
        baseline_volume=20,
        current_sentiment=0.7,
        baseline_sentiment=0.2,
        unique_authors=150,
    )

    assert surging_res.growth_rate_pct >= 800.0
    assert surging_res.acceleration_status == "surging"
    assert surging_res.sentiment_velocity == 0.5
    assert surging_res.anomaly_detected is True
    assert "Unusual volume surge" in surging_res.explanation


@pytest.mark.anyio
async def test_trending_project_discovery_multi_signal():
    """Verify trending discovery produces transparent reasons without fabricated metrics."""
    discovery = TrendingDiscoveryEngine()
    fake_news = [
        {"title": "Virtuals Protocol reaches milestone in AI Agent ecosystems", "snippet": "Framework update brings massive adoption."},
        {"title": "Render Network decentralizes compute cluster across Solana", "snippet": "DePIN hardware usage surges."},
    ]

    results = await discovery.discover_trending_projects(news_articles=fake_news)
    assert len(results) > 0

    for proj in results:
        assert proj.name is not None
        assert proj.symbol is not None
        assert proj.discovery_reason != ""
        assert proj.mindshare_pct >= 0.0
        assert proj.sentiment_label in [SentimentClass.POSITIVE, SentimentClass.NEGATIVE, SentimentClass.NEUTRAL, SentimentClass.MIXED]


def test_smart_alert_rule_evaluation_and_cooldown():
    """Verify alert rule evaluation, threshold triggers, and cooldown suppression."""
    alert_engine = ScannerAlertEngine()
    rule = ScannerAlertRule(
        rule_id="test-rule-1",
        user_id="user_123",
        rule_type="narrative_spike",
        target_entity="AI Agents",
        threshold=40.0,
        cooldown_minutes=60,
    )

    # 1. First trigger should fire an alert event
    ev1 = alert_engine.evaluate_narrative_event(
        rule=rule,
        narrative_name="Autonomous AI Agents",
        momentum_pct=65.0,
    )
    assert ev1 is not None
    assert ev1.severity in [AlertSeverity.HIGH, AlertSeverity.MEDIUM, AlertSeverity.CRITICAL]
    assert "Narrative Surge Alert" in ev1.title

    # 2. Second trigger immediately after should be suppressed by cooldown
    ev2 = alert_engine.evaluate_narrative_event(
        rule=rule,
        narrative_name="Autonomous AI Agents",
        momentum_pct=75.0,
    )
    assert ev2 is None  # Suppressed by 60m cooldown


def test_intelligence_report_facts_vs_interpretations_separation():
    """Verify automated research reports clearly separate empirical data from analytical interpretation."""
    report = IntelligenceReportGenerator.generate_research_report(
        topic="Virtuals Protocol",
        entity_type="project",
        market_data={"found": True, "price_usd": 1.45, "volume_24h_usd": 25000000, "liquidity_usd": 8500000, "market_cap": 1400000000},
        sentiment_data={"primary_sentiment": "positive", "sentiment_score": 0.45, "total_samples": 40, "unique_authors": 32, "coordinated_activity_flag": False},
        sources=[{"title": "Virtuals GitBook", "url": "https://virtuals.io", "domain": "Official"}],
    )

    assert "virtuals protocol" in report.title.lower()
    assert report.executive_summary != ""
    assert "Current Price:" in report.market_and_mindshare
    assert "Primary Sentiment" in report.sentiment_analysis and "POSITIVE" in report.sentiment_analysis
    assert "Confidence Level:" in report.limitations_and_confidence
    assert "does not constitute financial advice" in report.limitations_and_confidence
    assert len(report.important_sources) == 1
