"""RSS/Atom connector — parses feeds via feedparser + httpx."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.connectors.base import BaseConnector, RawItemData
from ai_digest.models.source import Source

logger = logging.getLogger(__name__)


class RSSConnector(BaseConnector):
    """Fetch and parse RSS/Atom feeds."""

    async def fetch(
        self,
        source: Source,
        http_client: httpx.AsyncClient,
        db: AsyncSession,
    ) -> list[RawItemData]:
        headers: dict[str, str] = {}
        parse_rules = source.parse_rules or {}

        # Conditional fetch using ETag / Last-Modified from parse_rules
        if etag := parse_rules.get("etag"):
            headers["If-None-Match"] = etag
        if last_modified := parse_rules.get("last_modified"):
            headers["If-Modified-Since"] = last_modified

        try:
            resp = await http_client.get(source.source_url, headers=headers, timeout=30)
        except httpx.HTTPError as exc:
            logger.warning("RSS fetch failed for %s: %s", source.source_url, exc)
            return []

        if resp.status_code == 304:
            logger.debug("RSS %s not modified (304)", source.source_url)
            return []

        if resp.status_code >= 400:
            logger.warning("RSS %s returned %d", source.source_url, resp.status_code)
            return []

        feed = feedparser.parse(resp.text)

        items: list[RawItemData] = []
        for entry in feed.entries:
            published_at = _parse_date(entry)
            content_text = _extract_content(entry)
            items.append(
                RawItemData(
                    external_id=entry.get("id") or entry.get("link"),
                    url=entry.get("link", source.source_url),
                    title=entry.get("title"),
                    content_text=content_text,
                    content_html=_extract_html(entry),
                    published_at=published_at,
                )
            )

        logger.info("RSS %s → %d items", source.source_url, len(items))
        return items


def _parse_date(entry) -> datetime | None:
    """Try to extract a timezone-aware datetime from a feed entry."""
    for field in ("published", "updated"):
        raw = entry.get(field)
        if not raw:
            continue
        try:
            return parsedate_to_datetime(raw)
        except Exception:
            pass
        # feedparser parsed struct
        parsed = entry.get(f"{field}_parsed")
        if parsed:
            try:
                from time import mktime
                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
            except Exception:
                pass
    return None


def _extract_content(entry) -> str | None:
    """Get plain-text content from feed entry, stripping HTML tags."""
    import re
    raw = None
    # Prefer summary, fall back to content
    if summary := entry.get("summary"):
        raw = summary
    else:
        content_list = entry.get("content", [])
        if content_list:
            raw = content_list[0].get("value")
    if not raw:
        return None
    # Strip HTML tags — RSS feeds (esp. Reddit) embed raw HTML
    clean = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", clean).strip() or raw


def _extract_html(entry) -> str | None:
    """Get HTML content if available."""
    content_list = entry.get("content", [])
    for c in content_list:
        if "html" in c.get("type", ""):
            return c.get("value")
    return None
