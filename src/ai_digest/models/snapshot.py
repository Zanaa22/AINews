"""Snapshot ORM model — HTML snapshots for diff-based sources."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.source_id"), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    diff_from_prev: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_changes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_snapshots_source", "source_id", "fetched_at"),
    )

    def __repr__(self) -> str:
        return f"<Snapshot {self.source_id} @ {self.fetched_at}>"
