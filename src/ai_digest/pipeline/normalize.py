"""Normalize raw items into canonical UpdateEvent form."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from ai_digest.connectors.base import RawItemData
from ai_digest.models.raw_item import RawItem
from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_ALPHA_RE = re.compile(r"[A-Za-z]{2,}")
_REPO_RE = re.compile(r"([\w.-]+)\s*/\s*([\w.-]+)")


def _strip_markup(text: str) -> str:
    clean = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", clean).strip()


def _is_readable(text: str, min_words: int = 3) -> bool:
    words = text.split()
    if len(words) < min_words:
        return False
    alpha_words = sum(1 for w in words if _ALPHA_RE.search(w))
    return alpha_words / len(words) > 0.3


def _extract_repo_title(text: str) -> str | None:
    m = _REPO_RE.search(text)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}"


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
    content_text = raw.content_text or ""
    if not title or not _is_readable(title, min_words=1):
        repo = _extract_repo_title(title) or _extract_repo_title(content_text)
        if repo:
            title = repo
        else:
            clean = _strip_markup(content_text)
            if clean and _is_readable(clean, min_words=2):
                title = clean[:100].strip()
            else:
                title = f"{source.company_name} update"

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
