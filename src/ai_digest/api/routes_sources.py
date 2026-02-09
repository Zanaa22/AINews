"""Source registry API routes — CRUD for ingestion sources."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.database import get_session
from ai_digest.models.source import Source

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    company_slug: str
    company_name: str
    product_line: str | None = None
    source_name: str
    source_url: str
    fetch_method: str
    poll_frequency_min: int = 60
    trust_tier: int = 1
    priority: str = "normal"
    parse_rules: dict = {}
    enabled: bool = True
    notes: str | None = None


class SourceUpdate(BaseModel):
    company_slug: str | None = None
    company_name: str | None = None
    product_line: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    fetch_method: str | None = None
    poll_frequency_min: int | None = None
    trust_tier: int | None = None
    priority: str | None = None
    parse_rules: dict | None = None
    enabled: bool | None = None
    notes: str | None = None


@router.get("")
async def list_sources(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_session),
):
    """List all sources."""
    stmt = select(Source).order_by(Source.company_slug, Source.source_name)
    if enabled_only:
        stmt = stmt.where(Source.enabled.is_(True))
    result = await db.execute(stmt)
    sources = result.scalars().all()

    return [_source_to_dict(s) for s in sources]


@router.get("/{source_id}")
async def get_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
):
    """Get a single source by ID."""
    result = await db.execute(
        select(Source).where(Source.source_id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_to_dict(source)


@router.post("", status_code=201)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new source."""
    source = Source(
        source_id=uuid.uuid4(),
        **body.model_dump(),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return _source_to_dict(source)


@router.patch("/{source_id}")
async def update_source(
    source_id: uuid.UUID,
    body: SourceUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update an existing source."""
    result = await db.execute(
        select(Source).where(Source.source_id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)
    source.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(source)
    return _source_to_dict(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
):
    """Delete a source."""
    result = await db.execute(
        select(Source).where(Source.source_id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()


def _source_to_dict(source: Source) -> dict:
    return {
        "source_id": str(source.source_id),
        "company_slug": source.company_slug,
        "company_name": source.company_name,
        "product_line": source.product_line,
        "source_name": source.source_name,
        "source_url": source.source_url,
        "fetch_method": source.fetch_method,
        "poll_frequency_min": source.poll_frequency_min,
        "trust_tier": source.trust_tier,
        "priority": source.priority,
        "parse_rules": source.parse_rules,
        "health_status": source.health_status,
        "last_fetched_at": source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        "last_item_at": source.last_item_at.isoformat() if source.last_item_at else None,
        "enabled": source.enabled,
        "notes": source.notes,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }
