"""Digest ORM model — generated daily digests."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, Index, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_digest.database import Base


class Digest(Base):
    __tablename__ = "digests"

    digest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    digest_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    overview_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    delivery_channels: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    html_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    web_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        Index("idx_digests_date", "digest_date"),
    )

    def __repr__(self) -> str:
        return f"<Digest {self.digest_date}>"
