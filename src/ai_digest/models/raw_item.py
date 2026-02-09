"""RawItem ORM model — ingested items before processing."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class RawItem(Base):
    __tablename__ = "raw_items"

    raw_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.source_id"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    snapshot_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_raw_items_source", "source_id", "fetched_at"),
        Index("idx_raw_items_hash", "content_hash"),
        Index("idx_raw_items_url", "url"),
        Index("idx_raw_items_published", "published_at"),
        UniqueConstraint("source_id", "external_id", name="uq_raw_items_source_ext"),
    )

    def __repr__(self) -> str:
        return f"<RawItem {self.title!r}>"
