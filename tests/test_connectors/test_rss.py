"""Tests for RSS connector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_digest.connectors.rss import RSSConnector


@pytest.fixture
def rss_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Feed</title>
        <item>
          <title>New Feature Released</title>
          <link>https://example.com/post/1</link>
          <description>We released a new feature.</description>
          <guid>post-1</guid>
          <pubDate>Mon, 09 Feb 2026 10:00:00 GMT</pubDate>
        </item>
        <item>
          <title>Bug Fix v1.2</title>
          <link>https://example.com/post/2</link>
          <description>Fixed a critical bug.</description>
          <guid>post-2</guid>
          <pubDate>Sun, 08 Feb 2026 15:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>"""


@pytest.mark.asyncio
async def test_rss_connector_parses_feed(rss_xml, sample_source):
    connector = RSSConnector()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = rss_xml

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_db = AsyncMock()

    items = await connector.fetch(sample_source, mock_client, mock_db)

    assert len(items) == 2
    assert items[0].title == "New Feature Released"
    assert items[0].url == "https://example.com/post/1"
    assert items[0].external_id == "post-1"
    assert items[1].title == "Bug Fix v1.2"


@pytest.mark.asyncio
async def test_rss_connector_handles_304(sample_source):
    connector = RSSConnector()

    mock_response = MagicMock()
    mock_response.status_code = 304

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_db = AsyncMock()

    items = await connector.fetch(sample_source, mock_client, mock_db)
    assert items == []


@pytest.mark.asyncio
async def test_rss_connector_handles_error(sample_source):
    connector = RSSConnector()

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_db = AsyncMock()

    items = await connector.fetch(sample_source, mock_client, mock_db)
    assert items == []
