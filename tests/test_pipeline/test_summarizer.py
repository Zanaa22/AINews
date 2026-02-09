"""Tests for summarizer pipeline stage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.models.update_event import UpdateEvent
from ai_digest.pipeline.summarizer import _parse_llm_json, _set_fallback_summary


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


def test_parse_llm_json_direct():
    text = '{"title": "Test", "what_changed": [], "confidence": "confirmed"}'
    result = _parse_llm_json(text)
    assert result is not None
    assert result["title"] == "Test"


def test_parse_llm_json_with_code_fence():
    text = '```json\n{"title": "Test"}\n```'
    result = _parse_llm_json(text)
    assert result is not None
    assert result["title"] == "Test"


def test_parse_llm_json_with_surrounding_text():
    text = 'Here is the summary:\n{"title": "Test"}\nDone.'
    result = _parse_llm_json(text)
    assert result is not None
    assert result["title"] == "Test"


def test_parse_llm_json_invalid():
    result = _parse_llm_json("This is not JSON at all")
    assert result is None


def test_fallback_summary():
    event = _make_event(title="Something happened with the API")
    _set_fallback_summary(event)
    assert event.summary_short == "Something happened with the API"
    assert event.summary_medium == "Something happened with the API"
