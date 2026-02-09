"""Tests for section allocation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.digest.sections import DigestSections, allocate_sections
from ai_digest.models.update_event import UpdateEvent


def _make_event(title: str, score: float, categories: list[str] = None, trust_tier: int = 1) -> UpdateEvent:
    return UpdateEvent(
        event_id=uuid.uuid4(),
        source_id=uuid.uuid4(),
        raw_item_id=uuid.uuid4(),
        company_slug="testco",
        company_name="TestCo",
        title=title,
        categories=categories or [],
        trust_tier=trust_tier,
        severity="HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW",
        breaking_change=False,
        impact_score=score,
        confidence="confirmed",
        citations=["https://example.com"],
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


def test_allocate_empty():
    sections = allocate_sections([])
    assert sections.total_count == 0


def test_allocate_top5():
    events = [_make_event(f"Event {i}", 1.0 - i * 0.1) for i in range(7)]
    sections = allocate_sections(events)
    assert len(sections.top5) == 5
    assert len(sections.everything_else) == 2


def test_allocate_developer_section():
    events = [
        _make_event("Top event", 0.9),
        _make_event("Top event 2", 0.85),
        _make_event("Top event 3", 0.8),
        _make_event("Top event 4", 0.75),
        _make_event("Top event 5", 0.7),
        _make_event("SDK Update", 0.5, ["SDK releases/updates"]),
        _make_event("API Change", 0.45, ["API changes (endpoints/auth/schemas)"]),
    ]
    sections = allocate_sections(events)
    assert len(sections.top5) == 5
    assert len(sections.developer) == 2


def test_allocate_radar():
    events = [_make_event(f"Top {i}", 0.9 - i * 0.05) for i in range(5)]
    events.append(_make_event("Community tool", 0.3, trust_tier=4))
    sections = allocate_sections(events)
    assert len(sections.radar) == 1
    assert sections.radar[0].title == "Community tool"


def test_sections_to_dict():
    sections = DigestSections()
    d = sections.to_dict()
    assert isinstance(d, dict)
    assert "top5" in d
    assert "everything_else" in d
