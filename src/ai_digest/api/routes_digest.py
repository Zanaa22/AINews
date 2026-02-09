"""Digest API routes — browse and retrieve generated digests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.config import settings
from ai_digest.database import get_session
from ai_digest.models.digest import Digest

router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("")
async def list_digests(
    limit: int = 30,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
):
    """List recent digests."""
    stmt = (
        select(Digest)
        .order_by(Digest.digest_date.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    digests = result.scalars().all()

    return [
        {
            "digest_id": str(d.digest_id),
            "digest_date": d.digest_date.isoformat(),
            "event_count": d.event_count,
            "generated_at": d.generated_at.isoformat() if d.generated_at else None,
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            "delivery_channels": d.delivery_channels,
            "web_url": d.web_url,
        }
        for d in digests
    ]


@router.get("/{digest_date}")
async def get_digest(
    digest_date: date,
    db: AsyncSession = Depends(get_session),
):
    """Get a single digest by date."""
    stmt = select(Digest).where(Digest.digest_date == digest_date)
    result = await db.execute(stmt)
    digest = result.scalar_one_or_none()

    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")

    return {
        "digest_id": str(digest.digest_id),
        "digest_date": digest.digest_date.isoformat(),
        "overview_text": digest.overview_text,
        "sections": digest.sections,
        "event_count": digest.event_count,
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None,
        "delivered_at": digest.delivered_at.isoformat() if digest.delivered_at else None,
        "delivery_channels": digest.delivery_channels,
        "web_url": digest.web_url,
    }


@router.get("/{digest_date}/html", response_class=HTMLResponse)
async def get_digest_html(digest_date: date):
    """Serve the rendered HTML digest page."""
    output_dir = Path(settings.web_output_dir)
    filepath = output_dir / f"digest-{digest_date.isoformat()}.html"

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Digest HTML not found")

    return HTMLResponse(content=filepath.read_text(encoding="utf-8"))
