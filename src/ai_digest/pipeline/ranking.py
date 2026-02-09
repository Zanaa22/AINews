"""Ranking — compute ImpactScore and assign severity for each UpdateEvent."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from ai_digest.models.update_event import UpdateEvent
from ai_digest.taxonomy import (
    ALWAYS_HIGH_CATEGORIES,
    CATEGORIES,
    IMPACT_WEIGHTS,
    RECENCY_LAMBDA,
    SEVERITY_SCORES,
    TRUST_SCORES,
)

logger = logging.getLogger(__name__)


async def rank_events(events: list[UpdateEvent]) -> list[UpdateEvent]:
    """Compute impact_score and assign severity for each event."""
    for event in events:
        # Assign severity first (needed for score computation)
        event.severity = _assign_severity(event)
        event.impact_score = _compute_impact_score(event)

    # Sort by impact_score descending
    events.sort(key=lambda e: e.impact_score, reverse=True)
    logger.info("Ranked %d events (top score: %.3f)", len(events),
                events[0].impact_score if events else 0)
    return events


def _assign_severity(event: UpdateEvent) -> str:
    """Rule-based severity assignment."""
    cats = set(event.categories)

    # Category 1 (New foundation model release) is always HIGH
    cat_ids = set()
    for cat_id, cat_name in CATEGORIES.items():
        if cat_name in cats:
            cat_ids.add(cat_id)

    if cat_ids & ALWAYS_HIGH_CATEGORIES:
        return "HIGH"

    # Breaking changes are always HIGH
    if event.breaking_change:
        return "HIGH"

    # Keywords that push to HIGH
    title_lower = event.title.lower()
    high_keywords = [
        "outage", "breach", "security incident", "deprecat",
        "end of life", "major release", "breaking",
    ]
    if any(kw in title_lower for kw in high_keywords):
        return "HIGH"

    # Keywords for MEDIUM
    medium_keywords = [
        "new feature", "update", "release", "upgrade",
        "support", "launch", "available", "introduces",
    ]
    if any(kw in title_lower for kw in medium_keywords):
        return "MEDIUM"

    # Trust tier 1 sources with SDKs/APIs default to MEDIUM
    if event.trust_tier == 1 and cats & {
        "SDK releases/updates",
        "API changes (endpoints/auth/schemas)",
    }:
        return "MEDIUM"

    return "LOW"


def _compute_impact_score(event: UpdateEvent) -> float:
    """Compute the weighted ImpactScore (0.0 – 1.0 range)."""
    w = IMPACT_WEIGHTS

    # Trust
    trust = TRUST_SCORES.get(event.trust_tier, 0.2)

    # Severity
    severity = SEVERITY_SCORES.get(event.severity, 0.15)

    # UserMatch — Phase 1: always 0.5 (no user preferences yet)
    user_match = 0.5

    # Recency: exp(-lambda * hours_old)
    now = datetime.now(timezone.utc)
    published = event.published_at or event.created_at
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    hours_old = max((now - published).total_seconds() / 3600, 0)
    recency = math.exp(-RECENCY_LAMBDA * hours_old)

    # Breadth — Phase 1: single source per event, normalised as 1/3
    breadth = 1.0 / 3.0

    # Novelty — Phase 1: assume novel (no historical cluster check yet)
    novelty = 1.0

    # SpamDupePenalty — Phase 1: 0 (no spam detection yet)
    spam_penalty = 0.0

    score = (
        w["trust"] * trust
        + w["severity"] * severity
        + w["user_match"] * user_match
        + w["recency"] * recency
        + w["breadth"] * breadth
        + w["novelty"] * novelty
        - w["spam_dupe_penalty"] * spam_penalty
    )

    return round(min(max(score, 0.0), 1.0), 4)
