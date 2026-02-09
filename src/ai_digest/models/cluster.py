"""Cluster ORM model — groups of related update events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canonical_title: Mapped[str] = mapped_column(Text, nullable=False)
    company_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    merged_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        Index("idx_clusters_company", "company_slug", "last_seen_at"),
    )

    def __repr__(self) -> str:
        return f"<Cluster {self.canonical_title!r}>"
