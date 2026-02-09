#!/usr/bin/env python3
"""Run the full ingestion + pipeline for all enabled sources (one-shot)."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_digest.config import settings
from ai_digest.scheduler.jobs import fetch_source_job, pipeline_job
from ai_digest.database import async_session_factory
from ai_digest.models.source import Source
from sqlalchemy import select

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting one-shot pipeline run")

    # 1. Fetch from all enabled sources
    async with async_session_factory() as db:
        result = await db.execute(
            select(Source).where(Source.enabled.is_(True))
        )
        sources = list(result.scalars().all())

    logger.info("Fetching from %d enabled sources...", len(sources))
    for source in sources:
        logger.info("  Fetching: %s (%s)", source.source_name, source.fetch_method)
        try:
            await fetch_source_job(str(source.source_id))
        except Exception as exc:
            logger.error("  Failed: %s", exc)

    # 2. Run pipeline
    logger.info("Running pipeline...")
    await pipeline_job()

    logger.info("Pipeline run complete")


if __name__ == "__main__":
    asyncio.run(main())
