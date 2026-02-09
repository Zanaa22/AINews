"""UpdateEvent ORM model — normalised, scored, summarised items."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class UpdateEvent(Base):
    __tablename__ = "update_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clusters.cluster_id"), nullable=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.source_id"), nullable=False
    )
    raw_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_items.raw_item_id"), nullable=False
    )
    company_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_line: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    categories: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    trust_tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False, default="LOW")
    breaking_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[str] = mapped_column(
        String(16), nullable=False, default="confirmed"
    )
    what_changed: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    citations: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    evidence_snippets: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    summary_short: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_medium: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    digest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("digests.digest_id"), nullable=True
    )
    digest_section: Mapped[str | None] = mapped_column(String(32), nullable=True)

    __table_args__ = (
        Index("idx_events_company", "company_slug", "created_at"),
        Index("idx_events_score", "impact_score"),
        Index("idx_events_created", "created_at"),
        Index("idx_events_digest", "digest_id"),
        Index("idx_events_severity", "severity", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<UpdateEvent {self.title!r} [{self.severity}]>"
