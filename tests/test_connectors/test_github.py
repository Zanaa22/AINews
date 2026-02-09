"""Tests for GitHub releases connector."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_digest.connectors.github_releases import GitHubReleasesConnector, _extract_owner_repo


def test_extract_owner_repo():
    assert _extract_owner_repo("https://github.com/openai/openai-python/releases") == "openai/openai-python"
    assert _extract_owner_repo("https://github.com/openai/openai-python") == "openai/openai-python"
    assert _extract_owner_repo("https://github.com/meta-llama") is None


@pytest.mark.asyncio
async def test_github_connector_parses_releases(sample_source):
    connector = GitHubReleasesConnector()
    sample_source.source_url = "https://github.com/testco/test-sdk/releases"

    releases_json = [
        {
            "id": 12345,
            "tag_name": "v2.0.0",
            "name": "v2.0.0 — Major Release",
            "html_url": "https://github.com/testco/test-sdk/releases/tag/v2.0.0",
            "body": "Breaking changes in this release.",
            "published_at": "2026-02-09T10:00:00Z",
            "prerelease": False,
            "draft": False,
        },
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = releases_json

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_db = AsyncMock()

    items = await connector.fetch(sample_source, mock_client, mock_db)

    assert len(items) == 1
    assert items[0].title == "v2.0.0 — Major Release"
    assert items[0].external_id == "12345"
    assert items[0].metadata.get("tag_name") == "v2.0.0"
