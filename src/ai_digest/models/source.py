"""Source ORM model — the source registry."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_line: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    fetch_method: Mapped[str] = mapped_column(String(32), nullable=False)  # rss|html_diff|...
    poll_frequency_min: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    trust_tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    parse_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    health_status: Mapped[str] = mapped_column(String(16), nullable=False, default="healthy")
    last_fetched_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_item_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        Index("idx_sources_company", "company_slug"),
        Index("idx_sources_enabled", "enabled", "health_status"),
        Index("idx_sources_next_fetch", "enabled", "last_fetched_at", "poll_frequency_min"),
    )

    def __repr__(self) -> str:
        return f"<Source {self.company_slug}/{self.source_name}>"
