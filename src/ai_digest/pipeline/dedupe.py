"""Deduplication — hard dedup (content hash) + soft dedup (title similarity)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.models.cluster import Cluster
from ai_digest.models.raw_item import RawItem
from ai_digest.models.update_event import UpdateEvent

logger = logging.getLogger(__name__)

# Title similarity threshold for soft dedup
SIMILARITY_THRESHOLD = 0.85


async def hard_dedupe(content_hash: str, db: AsyncSession) -> bool:
    """Return True if a RawItem with the same content_hash already exists."""
    stmt = select(RawItem.raw_item_id).where(RawItem.content_hash == content_hash).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def soft_dedupe_and_cluster(
    events: list[UpdateEvent],
    db: AsyncSession,
) -> list[UpdateEvent]:
    """Group similar events into clusters using title similarity.

    Returns the list of events with cluster_id set on clustered items.
    The "representative" event for each cluster is the one with the highest trust_tier.
    """
    if not events:
        return events

    # Build clusters from title similarity
    clusters: list[list[int]] = []  # each cluster is a list of indices
    assigned: set[int] = set()

    for i in range(len(events)):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)
        for j in range(i + 1, len(events)):
            if j in assigned:
                continue
            sim = _title_similarity(events[i].title, events[j].title)
            if sim >= SIMILARITY_THRESHOLD:
                cluster.append(j)
                assigned.add(j)
        if len(cluster) > 1:
            clusters.append(cluster)

    # Create Cluster rows and assign cluster_id to events
    for cluster_indices in clusters:
        cluster_events = [events[idx] for idx in cluster_indices]
        # Pick the event with the best (lowest) trust_tier as canonical
        canonical = min(cluster_events, key=lambda e: e.trust_tier)
        now = datetime.now(timezone.utc)

        cluster_obj = Cluster(
            cluster_id=uuid.uuid4(),
            canonical_title=canonical.title,
            company_slug=canonical.company_slug,
            event_count=len(cluster_events),
            first_seen_at=min(e.published_at or now for e in cluster_events),
            last_seen_at=max(e.published_at or now for e in cluster_events),
        )
        db.add(cluster_obj)

        for event in cluster_events:
            event.cluster_id = cluster_obj.cluster_id

        logger.info(
            "Clustered %d events under %r",
            len(cluster_events),
            canonical.title,
        )

    return events


def _title_similarity(a: str, b: str) -> float:
    """Compute normalised title similarity."""
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()
    if not a_lower or not b_lower:
        return 0.0
    return SequenceMatcher(None, a_lower, b_lower).ratio()
