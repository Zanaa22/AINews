"""Normalize raw items into canonical UpdateEvent form."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from ai_digest.connectors.base import RawItemData
from ai_digest.models.raw_item import RawItem
from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent

logger = logging.getLogger(__name__)


def normalize_item(
    raw: RawItemData,
    raw_item: RawItem,
    source: Source,
) -> UpdateEvent:
    """Convert a RawItemData + persisted RawItem into a skeleton UpdateEvent.

    Fields that require further processing (categories, severity, summary, etc.)
    are left at defaults and filled in by later pipeline stages.
    """
    title = (raw.title or "").strip()
    if not title:
        # Fallback: first 100 chars of content
        title = (raw.content_text or "")[:100].strip() or "Untitled"

    return UpdateEvent(
        event_id=uuid.uuid4(),
        source_id=source.source_id,
        raw_item_id=raw_item.raw_item_id,
        company_slug=source.company_slug,
        company_name=source.company_name,
        product_line=source.product_line,
        title=title,
        categories=[],
        trust_tier=source.trust_tier,
        severity="LOW",
        breaking_change=False,
        impact_score=0.0,
        confidence=_initial_confidence(source.trust_tier),
        citations=[raw.url],
        published_at=raw.published_at or datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


async def normalize_batch(
    items: list[tuple[RawItemData, RawItem]],
    source: Source,
) -> list[UpdateEvent]:
    """Normalize a batch of raw items into UpdateEvents."""
    events = []
    for raw, raw_item in items:
        event = normalize_item(raw, raw_item, source)
        events.append(event)
    logger.info("Normalized %d items from %s", len(events), source.source_name)
    return events


def _initial_confidence(trust_tier: int) -> str:
    if trust_tier == 1:
        return "confirmed"
    if trust_tier == 2:
        return "likely"
    return "unverified"
