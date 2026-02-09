"""Tests for digest generator."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.digest.generator import _generate_overview
from ai_digest.digest.sections import DigestSections
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


def test_generate_overview_with_events():
    sections = DigestSections()
    sections.top5 = [
        _make_event("OpenAI releases GPT-5", 0.95),
        _make_event("Anthropic raises API prices", 0.9),
        _make_event("Google adds audio to Gemini", 0.85),
    ]
    overview = _generate_overview(sections)
    assert overview.startswith("Today:")
    assert "TestCo" in overview  # company_name from _make_event
    assert "." in overview


def test_generate_overview_empty():
    sections = DigestSections()
    overview = _generate_overview(sections)
    assert "No major" in overview
