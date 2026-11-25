"""Data models and schemas for the Zoe Advanced Scanner and Intelligence Layer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SentimentClass(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNCERTAIN = "uncertain"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NarrativeRecord(BaseModel):
    id: str
    name: str
    category: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    status: str = "active"  # emerging, accelerating, steady, declining
    current_frequency: int = 0
    historical_frequency: int = 0
    momentum_pct: float = 0.0
    mindshare_pct: float = 0.0
    sentiment_score: float = 0.0  # -1.0 to 1.0
    sentiment_label: SentimentClass = SentimentClass.NEUTRAL
    associated_projects: List[str] = Field(default_factory=list)
    sample_size: int = 0
    updated_at: str = ""


class TrendingProject(BaseModel):
    name: str
    symbol: str
    contract_address: Optional[str] = None
    chain: str = "Solana"
    narrative: str = "General"
    news_count: int = 0
    social_volume: int = 0
    unique_authors: int = 0
    mindshare_pct: float = 0.0
    momentum_pct: float = 0.0
    sentiment_label: SentimentClass = SentimentClass.NEUTRAL
    sentiment_score: float = 0.0
    price_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    discovery_reason: str = ""
    flags: List[str] = Field(default_factory=list)


class SentimentAnalysisResult(BaseModel):
    query: str
    primary_sentiment: SentimentClass
    sentiment_score: float  # -1.0 (very negative) to +1.0 (very positive)
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    mixed_count: int = 0
    uncertain_count: int = 0
    total_samples: int = 0
    unique_authors: int = 0
    spam_detected_count: int = 0
    coordinated_activity_flag: bool = False
    context_notes: str = ""
    sample_posts: List[Dict[str, Any]] = Field(default_factory=list)


class MindshareResult(BaseModel):
    category: str
    timeframe: str  # 24h, 7d, 30d
    total_mentions_in_category: int
    total_unique_authors: int
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "verified_live_data"
    sample_size: int = 0
    source_provenance: str = "Verified Web3 Publishers & RSS Feeds"
    measurement_window: str = "24h"
    methodology: str = (
        "Calculated as (project_weighted_mentions / total_category_mentions) * 100, "
        "where unique author diversity discounts duplicate posting frequency. Simulated baseline activity is disabled."
    )


class MomentumResult(BaseModel):
    entity_name: str
    entity_type: str  # narrative or project
    current_volume: int
    baseline_volume: int
    growth_rate_pct: float
    acceleration_status: str  # surging, accelerating, stable, decelerating
    sentiment_velocity: float  # change in sentiment score over period
    anomaly_detected: bool = False
    explanation: str = ""


class ScannerAlertRule(BaseModel):
    rule_id: str
    user_id: str
    project_id: Optional[str] = None
    rule_type: str  # narrative_spike, sentiment_shift, volume_surge, watchlist_drain
    target_entity: str  # specific project, narrative name, or "all"
    threshold: float
    cooldown_minutes: int = 60
    enabled: bool = True
    created_at: str = ""


class ScannerAlertEvent(BaseModel):
    event_id: str
    rule_id: Optional[str] = None
    user_id: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str
    message: str
    trigger_explanation: str
    supporting_sources: List[Dict[str, str]] = Field(default_factory=list)
    timestamp_utc: str
    is_read: bool = False


class IntelligenceReport(BaseModel):
    report_id: str
    title: str
    topic: str
    entity_type: str  # narrative or project
    executive_summary: str
    narrative_overview: str
    market_and_mindshare: str
    sentiment_analysis: str
    social_and_news_evidence: str
    important_sources: List[Dict[str, str]] = Field(default_factory=list)
    missing_information: str
    limitations_and_confidence: str
    created_at_utc: str
