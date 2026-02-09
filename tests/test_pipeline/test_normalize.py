"""Tests for normalize pipeline stage."""

from __future__ import annotations

import uuid

import pytest

from ai_digest.connectors.base import RawItemData
from ai_digest.models.raw_item import RawItem
from ai_digest.pipeline.normalize import normalize_batch, normalize_item


@pytest.mark.asyncio
async def test_normalize_batch(sample_source, sample_raw_items):
    pairs = []
    for raw_data in sample_raw_items:
        raw_item = RawItem(
            raw_item_id=uuid.uuid4(),
            source_id=sample_source.source_id,
            url=raw_data.url,
            content_hash=raw_data.content_hash,
        )
        pairs.append((raw_data, raw_item))

    events = await normalize_batch(pairs, sample_source)

    assert len(events) == 3
    assert events[0].title == "TestCo releases v2.0 API with breaking changes"
    assert events[0].company_slug == "testco"
    assert events[0].trust_tier == 1
    assert events[0].confidence == "confirmed"


def test_normalize_item_sets_confidence(sample_source):
    sample_source.trust_tier = 4
    raw_data = RawItemData(url="https://example.com", title="Test")
    raw_item = RawItem(
        raw_item_id=uuid.uuid4(),
        source_id=sample_source.source_id,
        url="https://example.com",
        content_hash="abc",
    )
    event = normalize_item(raw_data, raw_item, sample_source)
    assert event.confidence == "unverified"


def test_normalize_item_fallback_title(sample_source):
    raw_data = RawItemData(
        url="https://example.com",
        title="",
        content_text="Some content here about a change",
    )
    raw_item = RawItem(
        raw_item_id=uuid.uuid4(),
        source_id=sample_source.source_id,
        url="https://example.com",
        content_hash="abc",
    )
    event = normalize_item(raw_data, raw_item, sample_source)
    assert event.title == "Some content here about a change"
