"""BaseConnector ABC — interface for all ingestion connectors."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.models.source import Source


class RawItemData(BaseModel):
    """Pydantic data class returned by connectors (not persisted directly)."""

    external_id: str | None = None
    url: str
    title: str | None = None
    content_text: str | None = None
    content_html: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = {}

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of normalised content for dedup."""
        payload = (self.url + (self.content_text or self.title or "")).encode()
        return hashlib.sha256(payload).hexdigest()


class BaseConnector(ABC):
    """Abstract base for all source connectors.

    Each connector knows how to fetch data from one source type and return
    a list of ``RawItemData`` objects.
    """

    @abstractmethod
    async def fetch(
        self,
        source: Source,
        http_client: httpx.AsyncClient,
        db: AsyncSession,
    ) -> list[RawItemData]:
        """Fetch new items from the source.

        Parameters
        ----------
        source : Source
            The source registry row with URL, parse_rules, etc.
        http_client : httpx.AsyncClient
            Shared async HTTP client (for connection pooling / rate limiting).
        db : AsyncSession
            Database session (for reading previous snapshots, etc.).

        Returns
        -------
        list[RawItemData]
            Zero or more new items discovered in this fetch.
        """
