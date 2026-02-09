"""Tests for HTML diff connector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_digest.connectors.html_diff import HTMLDiffConnector


@pytest.mark.asyncio
async def test_html_diff_first_snapshot_returns_empty(sample_source):
    """First snapshot should be stored as baseline, returning no items."""
    connector = HTMLDiffConnector()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><p>Initial content</p></body></html>"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    # Mock DB: no previous snapshot
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()

    sample_source.fetch_method = "html_diff"
    items = await connector.fetch(sample_source, mock_client, mock_db)

    assert items == []
    mock_db.add.assert_called_once()  # snapshot was stored


@pytest.mark.asyncio
async def test_html_diff_handles_http_error(sample_source):
    connector = HTMLDiffConnector()

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_db = AsyncMock()

    items = await connector.fetch(sample_source, mock_client, mock_db)
    assert items == []
