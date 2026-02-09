"""API Poll connector — fetch from JSON APIs (Hacker News Algolia, Product Hunt, etc.)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.connectors.base import BaseConnector, RawItemData
from ai_digest.models.source import Source

logger = logging.getLogger(__name__)


class APIPollConnector(BaseConnector):
    """Poll a JSON API endpoint and extract items.

    Supports:
    - Hacker News Algolia API (auto-detected from URL)
    - Generic JSON endpoints (configured via parse_rules)
    """

    async def fetch(
        self,
        source: Source,
        http_client: httpx.AsyncClient,
        db: AsyncSession,
    ) -> list[RawItemData]:
        try:
            resp = await http_client.get(source.source_url, timeout=30)
        except httpx.HTTPError as exc:
            logger.warning("API poll failed for %s: %s", source.source_url, exc)
            return []

        if resp.status_code >= 400:
            logger.warning("API poll %s returned %d", source.source_url, resp.status_code)
            return []

        data = resp.json()

        # Detect API type and route to the right parser
        if "hn.algolia.com" in source.source_url:
            return _parse_hn_results(data, source)

        if "producthunt.com" in source.source_url:
            return _parse_generic_json(data, source)

        return _parse_generic_json(data, source)


def _parse_hn_results(data: dict, source: Source) -> list[RawItemData]:
    """Parse Hacker News Algolia API search results."""
    hits = data.get("hits", [])
    items: list[RawItemData] = []

    for hit in hits:
        created_at_str = hit.get("created_at")
        published_at = None
        if created_at_str:
            try:
                published_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

        items.append(
            RawItemData(
                external_id=hit.get("objectID"),
                url=story_url,
                title=hit.get("title"),
                content_text=hit.get("story_text") or hit.get("comment_text"),
                published_at=published_at,
                metadata={
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "author": hit.get("author"),
                    "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                },
            )
        )

    logger.info("HN API → %d items", len(items))
    return items


def _parse_generic_json(data: dict | list, source: Source) -> list[RawItemData]:
    """Parse a generic JSON API response using parse_rules for field mapping."""
    parse_rules = source.parse_rules or {}

    # Determine the list of items
    items_key = parse_rules.get("items_key")
    if isinstance(data, list):
        records = data
    elif items_key and isinstance(data, dict):
        records = data.get(items_key, [])
    elif isinstance(data, dict):
        # Try common keys
        for key in ("results", "items", "data", "posts", "hits"):
            if key in data and isinstance(data[key], list):
                records = data[key]
                break
        else:
            records = [data]
    else:
        records = []

    # Field mapping with sensible defaults
    url_field = parse_rules.get("url_field", "url")
    title_field = parse_rules.get("title_field", "title")
    id_field = parse_rules.get("id_field", "id")
    content_field = parse_rules.get("content_field", "description")
    date_field = parse_rules.get("date_field", "created_at")

    items: list[RawItemData] = []
    for record in records:
        if not isinstance(record, dict):
            continue

        published_at = None
        raw_date = record.get(date_field)
        if isinstance(raw_date, str):
            try:
                published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except ValueError:
                pass

        items.append(
            RawItemData(
                external_id=str(record.get(id_field, "")),
                url=record.get(url_field, source.source_url),
                title=record.get(title_field),
                content_text=record.get(content_field),
                published_at=published_at,
                metadata={
                    k: v for k, v in record.items()
                    if k not in {url_field, title_field, id_field, content_field, date_field}
                    and isinstance(v, (str, int, float, bool))
                },
            )
        )

    logger.info("API poll %s → %d items", source.source_url, len(items))
    return items
