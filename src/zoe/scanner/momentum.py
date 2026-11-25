"""Momentum Engine tracking velocity, acceleration, and unusual attention anomalies."""

from typing import Any, Dict, List, Optional
from zoe.scanner.models import MomentumResult
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.momentum")


class MomentumEngine:
    """Calculates rates of change and acceleration across projects and narratives."""

    @staticmethod
    def calculate_momentum(
        entity_name: str,
        entity_type: str,
        current_24h_volume: int,
        baseline_volume: int,
        current_sentiment: float = 0.0,
        baseline_sentiment: float = 0.0,
        unique_authors: int = 1,
    ) -> MomentumResult:
        """
        Calculate mathematical momentum and velocity.
        Growth Rate: ((current - baseline) / max(baseline, 1)) * 100
        Sentiment Velocity: current_sentiment - baseline_sentiment
        """
        if baseline_volume <= 0:
            growth_pct = 100.0 if current_24h_volume > 0 else 0.0
        else:
            growth_pct = round(((current_24h_volume - baseline_volume) / baseline_volume) * 100, 2)

        sentiment_velocity = round(current_sentiment - baseline_sentiment, 2)

        # Acceleration status classification
        if growth_pct >= 100.0 and current_24h_volume >= 15:
            acceleration_status = "surging"
        elif growth_pct >= 25.0:
            acceleration_status = "accelerating"
        elif growth_pct <= -25.0:
            acceleration_status = "decelerating"
        else:
            acceleration_status = "stable"

        # Anomaly detection: extreme surge (>250% growth) or sudden sentiment flip
        anomaly = False
        anomaly_reasons = []

        if growth_pct >= 250.0 and current_24h_volume >= 20:
            anomaly = True
            anomaly_reasons.append("Unusual volume surge (>250% over baseline)")

        if abs(sentiment_velocity) >= 0.6:
            anomaly = True
            anomaly_reasons.append("Extreme sentiment shift within 24 hours")

        author_ratio = (unique_authors / current_24h_volume) if current_24h_volume > 0 else 1.0
        if current_24h_volume >= 15 and author_ratio < 0.25:
            anomaly = True
            anomaly_reasons.append("Suspicious volume concentration (low unique author count)")

        explanation = (
            f"{entity_name} recorded {current_24h_volume} mentions in the last 24h "
            f"vs a 7-day baseline of {baseline_volume} ({growth_pct:+}% growth). "
            f"Sentiment velocity: {sentiment_velocity:+} points."
        )
        if anomaly:
            explanation += f" [ANOMALY DETECTED: {', '.join(anomaly_reasons)}]"

        return MomentumResult(
            entity_name=entity_name,
            entity_type=entity_type,
            current_volume=current_24h_volume,
            baseline_volume=baseline_volume,
            growth_rate_pct=growth_pct,
            acceleration_status=acceleration_status,
            sentiment_velocity=sentiment_velocity,
            anomaly_detected=anomaly,
            explanation=explanation,
        )
