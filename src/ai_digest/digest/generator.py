"""Digest generator — full workflow from querying events to rendered output."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

import anthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.config import settings
from ai_digest.digest.renderer import render_email_digest, render_web_digest
from ai_digest.digest.sections import DigestSections, allocate_sections
from ai_digest.models.digest import Digest
from ai_digest.models.update_event import UpdateEvent
from ai_digest.pipeline.dedupe import soft_dedupe_and_cluster
from ai_digest.pipeline.summarizer import summarize_batch

logger = logging.getLogger(__name__)


async def generate_digest(
    target_date: date,
    db: AsyncSession,
    anthropic_client: anthropic.AsyncAnthropic | None = None,
) -> Digest | None:
    """Generate the daily digest for ``target_date``.

    Steps:
    1. Query un-assigned events from the last 24h window.
    2. Re-cluster for late-arriving duplicates.
    3. Allocate into sections.
    4. Summarize any unsummarized events (LLM).
    5. Generate overview paragraph.
    6. Render email + web HTML.
    7. Store Digest row and mark events as assigned.
    """
    # Define the 24h window: previous day 08:00 ART → today 07:59:59 ART
    # ART = UTC-3
    tz_offset = timezone(timedelta(hours=-3))
    cutoff_start = datetime.combine(
        target_date - timedelta(days=1),
        datetime.strptime("08:00", "%H:%M").time(),
        tzinfo=tz_offset,
    )
    cutoff_end = datetime.combine(
        target_date,
        datetime.strptime("07:59:59", "%H:%M:%S").time(),
        tzinfo=tz_offset,
    )

    # 1. Query events
    stmt = (
        select(UpdateEvent)
        .where(
            UpdateEvent.created_at >= cutoff_start,
            UpdateEvent.created_at <= cutoff_end,
            UpdateEvent.digest_id.is_(None),
        )
        .order_by(UpdateEvent.impact_score.desc())
    )
    result = await db.execute(stmt)
    events = list(result.scalars().all())

    if not events:
        logger.warning("No events found for digest %s", target_date)
        return None

    logger.info("Found %d events for digest %s", len(events), target_date)

    # 2. Re-cluster
    events = await soft_dedupe_and_cluster(events, db)

    # 3. Allocate sections
    sections = allocate_sections(events)

    # 4. Summarize (if LLM client available)
    if anthropic_client:
        all_events = (
            sections.top5 + sections.developer + sections.models
            + sections.pricing + sections.incidents
        )
        await summarize_batch(all_events, anthropic_client, db)

    # 5. Generate overview
    overview = _generate_overview(sections)

    # 6. Render
    email_html = render_email_digest(target_date, overview, sections)
    web_html = render_web_digest(target_date, overview, sections)

    # 7. Store digest
    digest = Digest(
        digest_id=uuid.uuid4(),
        digest_date=target_date,
        overview_text=overview,
        sections=sections.to_dict(),
        event_count=sections.total_count,
        generated_at=datetime.now(timezone.utc),
    )
    db.add(digest)

    # Mark events as assigned to this digest
    event_ids = [e.event_id for e in events]
    await db.execute(
        update(UpdateEvent)
        .where(UpdateEvent.event_id.in_(event_ids))
        .values(digest_id=digest.digest_id)
    )

    await db.commit()

    logger.info(
        "Generated digest %s with %d events",
        target_date, sections.total_count,
    )

    # Attach rendered HTML as attributes for downstream use
    digest._email_html = email_html  # type: ignore[attr-defined]
    digest._web_html = web_html  # type: ignore[attr-defined]

    return digest


def _generate_overview(sections: DigestSections) -> str:
    """Generate a 1-paragraph overview from the top 5 events."""
    if not sections.top5:
        return "No major AI updates today."

    highlights = []
    for event in sections.top5[:3]:
        highlights.append(f"{event.company_name}: {event.title}")

    return "Today: " + ". ".join(highlights) + "."
