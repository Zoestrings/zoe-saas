"""Smart Alert Engine for user-configurable threshold monitoring and trigger events."""

import uuid
import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoe.scanner.models import AlertSeverity, ScannerAlertEvent, ScannerAlertRule
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.alerts")


class ScannerAlertEngine:
    """Evaluates rules against incoming market, narrative, and sentiment events."""

    def __init__(self):
        # In-memory cooldown tracker: (user_id, rule_type, target_entity) -> last_triggered_dt
        self._cooldowns: Dict[Tuple[str, str, str], datetime.datetime] = {}

    def is_in_cooldown(
        self,
        user_id: str,
        rule_type: str,
        target_entity: str,
        cooldown_minutes: int,
    ) -> bool:
        """Check if an alert is suppressed by an active cooldown window."""
        key = (user_id, rule_type, target_entity.lower())
        last_time = self._cooldowns.get(key)
        if not last_time:
            return False

        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - last_time).total_seconds() / 60.0
        return elapsed < cooldown_minutes

    def mark_triggered(self, user_id: str, rule_type: str, target_entity: str) -> None:
        """Record the trigger time for cooldown tracking."""
        key = (user_id, rule_type, target_entity.lower())
        self._cooldowns[key] = datetime.datetime.now(datetime.timezone.utc)

    def evaluate_narrative_event(
        self,
        rule: ScannerAlertRule,
        narrative_name: str,
        momentum_pct: float,
        supporting_sources: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[ScannerAlertEvent]:
        """Evaluate narrative momentum against user rule threshold."""
        if not rule.enabled:
            return None

        if rule.target_entity.lower() != "all" and rule.target_entity.lower() not in narrative_name.lower():
            return None

        if self.is_in_cooldown(rule.user_id, rule.rule_type, narrative_name, rule.cooldown_minutes):
            return None

        if momentum_pct >= rule.threshold:
            self.mark_triggered(rule.user_id, rule.rule_type, narrative_name)
            severity = AlertSeverity.CRITICAL if momentum_pct >= 100.0 else (
                AlertSeverity.HIGH if momentum_pct >= 50.0 else AlertSeverity.MEDIUM
            )
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            return ScannerAlertEvent(
                event_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                severity=severity,
                title=f"Narrative Surge Alert: {narrative_name}",
                message=f"Narrative '{narrative_name}' attention grew by {momentum_pct:+}% (Threshold: {rule.threshold}%).",
                trigger_explanation=(
                    f"Measured momentum of {momentum_pct:+}% exceeded your configured rule threshold of {rule.threshold}%."
                ),
                supporting_sources=supporting_sources or [],
                timestamp_utc=now_str,
                is_read=False,
            )
        return None

    def evaluate_sentiment_drop(
        self,
        rule: ScannerAlertRule,
        entity_name: str,
        sentiment_score: float,
        supporting_sources: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[ScannerAlertEvent]:
        """Evaluate negative sentiment swing."""
        if not rule.enabled:
            return None

        if rule.target_entity.lower() != "all" and rule.target_entity.lower() not in entity_name.lower():
            return None

        if self.is_in_cooldown(rule.user_id, rule.rule_type, entity_name, rule.cooldown_minutes):
            return None

        # Rule threshold for negative sentiment (e.g. score <= -0.3)
        if sentiment_score <= rule.threshold:
            self.mark_triggered(rule.user_id, rule.rule_type, entity_name)
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            return ScannerAlertEvent(
                event_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                severity=AlertSeverity.HIGH if sentiment_score <= -0.5 else AlertSeverity.MEDIUM,
                title=f"Negative Sentiment Shift: {entity_name}",
                message=f"Sentiment score for {entity_name} dropped to {sentiment_score:.2f} (Threshold: <= {rule.threshold:.2f}).",
                trigger_explanation=(
                    f"Sentiment dropped below your alert threshold of {rule.threshold:.2f} based on verified discussion samples."
                ),
                supporting_sources=supporting_sources or [],
                timestamp_utc=now_str,
                is_read=False,
            )
        return None
