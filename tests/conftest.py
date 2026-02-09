"""Test fixtures — sample data and helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.connectors.base import RawItemData
from ai_digest.models.source import Source


@pytest.fixture
def sample_source() -> Source:
    """A sample source for testing."""
    return Source(
        source_id=uuid.uuid4(),
        company_slug="testco",
        company_name="TestCo",
        product_line="API",
        source_name="TestCo Changelog",
        source_url="https://testco.com/changelog",
        fetch_method="rss",
        poll_frequency_min=60,
        trust_tier=1,
        priority="high",
        parse_rules={},
        health_status="healthy",
        enabled=True,
    )


@pytest.fixture
def sample_raw_items() -> list[RawItemData]:
    """Sample raw items for testing pipeline stages."""
    return [
        RawItemData(
            external_id="item-1",
            url="https://testco.com/changelog/1",
            title="TestCo releases v2.0 API with breaking changes",
            content_text="TestCo API v2.0 is now available. This release includes breaking changes to the /chat endpoint.",
            published_at=datetime.now(timezone.utc),
        ),
        RawItemData(
            external_id="item-2",
            url="https://testco.com/changelog/2",
            title="TestCo adds new embedding model",
            content_text="New embedding model testco-embed-v3 is now available with improved performance.",
            published_at=datetime.now(timezone.utc),
        ),
        RawItemData(
            external_id="item-3",
            url="https://testco.com/changelog/3",
            title="Minor SDK patch v1.2.3",
            content_text="Bug fix release for the Python SDK.",
            published_at=datetime.now(timezone.utc),
        ),
    ]
