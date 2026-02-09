"""Health check endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.database import get_session
from ai_digest.models.digest import Digest
from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_session)):
    """System health check with basic stats."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Source stats
    source_count = await db.scalar(select(func.count(Source.source_id)))
    enabled_count = await db.scalar(
        select(func.count(Source.source_id)).where(Source.enabled.is_(True))
    )

    # Event stats
    event_count = await db.scalar(select(func.count(UpdateEvent.event_id)))

    # Latest digest
    latest_digest = await db.scalar(
        select(Digest.digest_date).order_by(Digest.digest_date.desc()).limit(1)
    )

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "sources": {
            "total": source_count,
            "enabled": enabled_count,
        },
        "events_total": event_count,
        "latest_digest_date": latest_digest.isoformat() if latest_digest else None,
    }
