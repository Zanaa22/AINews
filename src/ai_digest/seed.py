"""Seed the source registry from CSV file."""

from __future__ import annotations

import csv
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.models.source import Source

logger = logging.getLogger(__name__)

DEFAULT_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "sources_seed.csv"


async def seed_sources(
    db: AsyncSession,
    csv_path: Path = DEFAULT_CSV,
) -> int:
    """Read sources from CSV and upsert into the database.

    Returns the number of sources created or updated.
    """
    if not csv_path.exists():
        logger.error("Seed CSV not found: %s", csv_path)
        return 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    count = 0
    for row in rows:
        source_url = row["source_url"].strip()
        if not source_url:
            continue

        # Check if source already exists by URL
        result = await db.execute(
            select(Source).where(Source.source_url == source_url)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing source
            existing.company_slug = row["company_slug"].strip() or "community"
            existing.company_name = row["company_name"].strip() or "Community"
            existing.product_line = row.get("product_line", "").strip() or None
            existing.source_name = row["source_name"].strip()
            existing.fetch_method = row["fetch_method"].strip()
            existing.poll_frequency_min = int(row.get("poll_freq_min", 60))
            existing.trust_tier = int(row.get("trust_tier", 1))
            existing.priority = row.get("priority", "normal").strip()
            count += 1
        else:
            # Create new source
            source = Source(
                source_id=uuid.uuid4(),
                company_slug=row["company_slug"].strip() or "community",
                company_name=row["company_name"].strip() or "Community",
                product_line=row.get("product_line", "").strip() or None,
                source_name=row["source_name"].strip(),
                source_url=source_url,
                fetch_method=row["fetch_method"].strip(),
                poll_frequency_min=int(row.get("poll_freq_min", 60)),
                trust_tier=int(row.get("trust_tier", 1)),
                priority=row.get("priority", "normal").strip(),
            )
            db.add(source)
            count += 1

    await db.commit()
    logger.info("Seeded %d sources from %s", count, csv_path)
    return count
