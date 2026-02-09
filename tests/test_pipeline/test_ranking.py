"""Tests for ranking pipeline stage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.models.update_event import UpdateEvent
from ai_digest.pipeline.ranking import _assign_severity, _compute_impact_score, rank_events


def _make_event(**kwargs) -> UpdateEvent:
    defaults = {
        "event_id": uuid.uuid4(),
        "source_id": uuid.uuid4(),
        "raw_item_id": uuid.uuid4(),
        "company_slug": "testco",
        "company_name": "TestCo",
        "title": "Test Event",
        "categories": [],
        "trust_tier": 1,
        "severity": "LOW",
        "breaking_change": False,
        "impact_score": 0.0,
        "confidence": "confirmed",
        "citations": ["https://example.com"],
        "published_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return UpdateEvent(**defaults)


def test_severity_breaking_change():
    event = _make_event(
        title="API v1 deprecated",
        breaking_change=True,
    )
    assert _assign_severity(event) == "HIGH"


def test_severity_new_model():
    event = _make_event(
        title="New model released",
        categories=["New foundation model release"],
    )
    assert _assign_severity(event) == "HIGH"


def test_severity_medium():
    event = _make_event(
        title="New feature available for developers",
        categories=["SDK releases/updates"],
    )
    assert _assign_severity(event) == "MEDIUM"


def test_severity_low():
    event = _make_event(
        title="Internal refactoring notes",
        categories=["Datasets (new/updated/licensing)"],
    )
    assert _assign_severity(event) == "LOW"


def test_impact_score_range():
    event = _make_event(severity="HIGH", trust_tier=1)
    score = _compute_impact_score(event)
    assert 0.0 <= score <= 1.0


def test_high_event_scores_higher():
    high_event = _make_event(severity="HIGH", trust_tier=1, breaking_change=True)
    low_event = _make_event(severity="LOW", trust_tier=4)
    high_event.severity = "HIGH"
    low_event.severity = "LOW"
    assert _compute_impact_score(high_event) > _compute_impact_score(low_event)


@pytest.mark.asyncio
async def test_rank_events_sorts():
    events = [
        _make_event(title="Low priority", categories=[], trust_tier=4),
        _make_event(title="Breaking change!", breaking_change=True, trust_tier=1),
    ]
    ranked = await rank_events(events)
    assert ranked[0].title == "Breaking change!"
    assert ranked[0].impact_score >= ranked[1].impact_score
