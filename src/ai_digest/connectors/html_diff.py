"""HTML-diff connector — fetch a page, diff against last snapshot, extract changes."""

from __future__ import annotations

import difflib
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.connectors.base import BaseConnector, RawItemData
from ai_digest.models.snapshot import Snapshot
from ai_digest.models.source import Source

logger = logging.getLogger(__name__)


class HTMLDiffConnector(BaseConnector):
    """Fetch an HTML page, diff against the previous snapshot, yield changed sections."""

    async def fetch(
        self,
        source: Source,
        http_client: httpx.AsyncClient,
        db: AsyncSession,
    ) -> list[RawItemData]:
        try:
            resp = await http_client.get(source.source_url, timeout=30)
        except httpx.HTTPError as exc:
            logger.warning("HTML fetch failed for %s: %s", source.source_url, exc)
            return []

        if resp.status_code >= 400:
            logger.warning("HTML %s returned %d", source.source_url, resp.status_code)
            return []

        html = resp.text
        content_hash = hashlib.sha256(html.encode()).hexdigest()

        # Get previous snapshot
        prev_stmt = (
            select(Snapshot)
            .where(Snapshot.source_id == source.source_id)
            .order_by(Snapshot.fetched_at.desc())
            .limit(1)
        )
        result = await db.execute(prev_stmt)
        prev_snapshot = result.scalar_one_or_none()

        # If same hash as previous, no changes
        if prev_snapshot and prev_snapshot.content_hash == content_hash:
            logger.debug("HTML %s unchanged", source.source_url)
            return []

        # Extract text from HTML
        soup = BeautifulSoup(html, "html.parser")
        parse_rules = source.parse_rules or {}
        css_selector = parse_rules.get("css_selector")

        if css_selector:
            target = soup.select_one(css_selector)
            current_text = target.get_text("\n", strip=True) if target else soup.get_text("\n", strip=True)
        else:
            current_text = soup.get_text("\n", strip=True)

        # Compute diff if we have a previous snapshot
        diff_text: str | None = None
        if prev_snapshot and prev_snapshot.diff_from_prev is not None:
            # We stored previous text in diff_from_prev as the full text last time
            pass

        # Store new snapshot
        new_snapshot = Snapshot(
            snapshot_id=uuid.uuid4(),
            source_id=source.source_id,
            s3_key=f"snapshots/{source.source_id}/{content_hash}.html",
            content_hash=content_hash,
            fetched_at=datetime.now(timezone.utc),
            diff_from_prev=current_text,  # store full text for next diff
            has_changes=True,
        )
        db.add(new_snapshot)

        # If no previous snapshot, treat entire page as new (return nothing —
        # we need a baseline first).
        if not prev_snapshot:
            logger.info("HTML %s first snapshot stored (baseline)", source.source_url)
            return []

        # Compute diff between previous text and current text
        prev_text = prev_snapshot.diff_from_prev or ""
        diff_lines = list(
            difflib.unified_diff(
                prev_text.splitlines(),
                current_text.splitlines(),
                lineterm="",
                n=2,
            )
        )

        if not diff_lines:
            logger.debug("HTML %s text unchanged despite hash diff", source.source_url)
            return []

        # Extract added lines as the "changes"
        added_lines = [
            line[1:] for line in diff_lines
            if line.startswith("+") and not line.startswith("+++")
        ]
        if not added_lines:
            return []

        change_text = "\n".join(added_lines)
        items = _split_changes_into_items(change_text, source)

        logger.info("HTML %s → %d changed items", source.source_url, len(items))
        return items


_REPO_RE = re.compile(r"([\w.-]+)\s*/\s*([\w.-]+)")


def _extract_title(block: str) -> str:
    """Extract a meaningful title from a diff block.

    For GitHub-trending-style content, tries to find owner/repo.
    Falls back to the first line with enough alpha chars.
    """
    m = _REPO_RE.search(block)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # Fall back to first line that has real words
    for line in block.split("\n"):
        line = line.strip()
        if len(line) > 10 and sum(c.isalpha() for c in line) > len(line) * 0.3:
            return line[:120]
    return block.split("\n")[0][:120]


def _split_changes_into_items(change_text: str, source: Source) -> list[RawItemData]:
    """Split a block of changed text into individual items.

    Uses a simple heuristic: split on blank lines or date-like headers.
    Each block becomes one RawItemData.
    """
    # Simple approach: treat the entire diff as a single item
    # More sophisticated parsing can be added via parse_rules
    blocks = [b.strip() for b in change_text.split("\n\n") if b.strip()]
    if not blocks:
        return []

    items: list[RawItemData] = []
    for i, block in enumerate(blocks):
        title = _extract_title(block)
        items.append(
            RawItemData(
                external_id=hashlib.sha256(block.encode()).hexdigest()[:16],
                url=source.source_url,
                title=title,
                content_text=block,
                published_at=datetime.now(timezone.utc),
            )
        )

    return items
