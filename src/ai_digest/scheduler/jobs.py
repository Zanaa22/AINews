"""APScheduler job definitions — fetch, pipeline, and digest generation."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

import anthropic
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from ai_digest.config import settings
from ai_digest.connectors.base import RawItemData
from ai_digest.connectors.factory import connector_for_source
from ai_digest.database import async_session_factory
from ai_digest.delivery.email_sender import send_digest_email
from ai_digest.delivery.web_publisher import publish_web_digest, rebuild_archive
from ai_digest.digest.generator import generate_digest
from ai_digest.models.raw_item import RawItem
from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent
from ai_digest.pipeline.dedupe import hard_dedupe, soft_dedupe_and_cluster
from ai_digest.pipeline.entity_resolution import resolve_entities
from ai_digest.pipeline.normalize import normalize_batch
from ai_digest.pipeline.ranking import rank_events
from ai_digest.pipeline.summarizer import summarize_batch

logger = logging.getLogger(__name__)


async def fetch_source_job(source_id: str) -> None:
    """Fetch new items from a single source and persist as RawItems."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Source).where(Source.source_id == source_id)
        )
        source = result.scalar_one_or_none()
        if not source or not source.enabled:
            return

        try:
            connector = connector_for_source(source.fetch_method)
        except ValueError as e:
            logger.error("No connector for source %s: %s", source.source_name, e)
            return

        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "AI-Digest-Bot/1.0"},
        ) as http_client:
            try:
                items = await connector.fetch(source, http_client, db)
            except Exception as exc:
                logger.error("Fetch failed for %s: %s", source.source_name, exc)
                return

        saved = 0
        for item_data in items:
            # Hard dedup check
            if await hard_dedupe(item_data.content_hash, db):
                continue

            raw_item = RawItem(
                raw_item_id=uuid.uuid4(),
                source_id=source.source_id,
                external_id=item_data.external_id,
                url=item_data.url,
                title=item_data.title,
                content_text=item_data.content_text,
                content_html=item_data.content_html,
                content_hash=item_data.content_hash,
                published_at=item_data.published_at,
                metadata_=item_data.metadata,
            )
            db.add(raw_item)
            saved += 1

        # Update source fetch timestamp
        source.last_fetched_at = datetime.now(timezone.utc)
        if items:
            latest = max(
                (i.published_at for i in items if i.published_at),
                default=None,
            )
            if latest:
                source.last_item_at = latest

        await db.commit()
        logger.info("Fetched %s: %d new / %d total", source.source_name, saved, len(items))


async def pipeline_job() -> None:
    """Process un-processed raw_items through the pipeline.

    Runs every 30 minutes. Finds raw items that don't have corresponding
    update_events yet and processes them: normalize → entity resolve → rank.
    """
    async with async_session_factory() as db:
        # Find sources with unprocessed items
        sources_stmt = select(Source).where(Source.enabled.is_(True))
        sources_result = await db.execute(sources_stmt)
        sources = list(sources_result.scalars().all())

        total_processed = 0

        for source in sources:
            # Find raw items without corresponding events
            from sqlalchemy import and_, exists

            has_event = (
                select(UpdateEvent.event_id)
                .where(UpdateEvent.raw_item_id == RawItem.raw_item_id)
                .exists()
            )

            unprocessed_stmt = (
                select(RawItem)
                .where(
                    RawItem.source_id == source.source_id,
                    ~has_event,
                    RawItem.is_duplicate.is_(False),
                )
                .limit(50)
            )
            result = await db.execute(unprocessed_stmt)
            raw_items = list(result.scalars().all())

            if not raw_items:
                continue

            # Build (RawItemData, RawItem) pairs for normalize
            pairs: list[tuple[RawItemData, RawItem]] = []
            for ri in raw_items:
                rid = RawItemData(
                    external_id=ri.external_id,
                    url=ri.url,
                    title=ri.title,
                    content_text=ri.content_text,
                    content_html=ri.content_html,
                    published_at=ri.published_at,
                    metadata=ri.metadata_ or {},
                )
                pairs.append((rid, ri))

            # Pipeline: normalize → entity resolve → rank → summarize
            events = await normalize_batch(pairs, source)
            events = await resolve_entities(events, source)
            events = await rank_events(events)
            events = await soft_dedupe_and_cluster(events, db)

            # Summarize if Anthropic key is available
            if settings.anthropic_api_key:
                anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key
                )
                await summarize_batch(events, anthropic_client, db)

            for event in events:
                db.add(event)

            total_processed += len(events)

        await db.commit()
        if total_processed:
            logger.info("Pipeline processed %d events", total_processed)


async def digest_job() -> None:
    """Generate and deliver today's digest."""
    today = date.today()

    # Create Anthropic client if key available
    anthropic_client = None
    if settings.anthropic_api_key:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async with async_session_factory() as db:
        digest = await generate_digest(today, db, anthropic_client)

        if not digest:
            logger.warning("No digest generated for %s (no events)", today)
            return

        # Deliver email
        email_html = getattr(digest, "_email_html", None)
        if email_html:
            sent = await send_digest_email(today, email_html)
            if sent:
                digest.delivered_at = datetime.now(timezone.utc)
                digest.delivery_channels = ["email"]

        # Publish web
        web_html = getattr(digest, "_web_html", None)
        if web_html:
            web_url = await publish_web_digest(today, web_html)
            digest.web_url = web_url
            if digest.delivery_channels:
                digest.delivery_channels.append("web")
            else:
                digest.delivery_channels = ["web"]

        await db.commit()

        # Rebuild archive
        await rebuild_archive()

        logger.info("Digest for %s generated and delivered", today)


def setup_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance.

    Returns the scheduler (not yet started — call scheduler.start() on app startup).
    """
    scheduler = AsyncIOScheduler(timezone=settings.digest_timezone)

    # Digest generation: daily at configured time
    hour, minute = settings.digest_time.split(":")
    scheduler.add_job(
        digest_job,
        "cron",
        hour=int(hour),
        minute=int(minute),
        id="digest_daily",
        name="Daily digest generation",
        replace_existing=True,
    )

    # Pipeline processing: every 30 minutes
    scheduler.add_job(
        pipeline_job,
        "interval",
        minutes=30,
        id="pipeline_30min",
        name="Pipeline processing",
        replace_existing=True,
    )

    return scheduler


async def schedule_fetch_jobs(scheduler: AsyncIOScheduler) -> None:
    """Add per-source fetch jobs based on the source registry.

    Should be called after the scheduler is started and DB is available.
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Source).where(Source.enabled.is_(True))
        )
        sources = list(result.scalars().all())

    for source in sources:
        job_id = f"fetch_{source.source_id}"
        scheduler.add_job(
            fetch_source_job,
            "interval",
            minutes=source.poll_frequency_min,
            args=[str(source.source_id)],
            id=job_id,
            name=f"Fetch {source.source_name}",
            replace_existing=True,
        )

    logger.info("Scheduled fetch jobs for %d sources", len(sources))
