"""GitHub Releases connector — fetch releases via the GitHub REST API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.config import settings
from ai_digest.connectors.base import BaseConnector, RawItemData
from ai_digest.models.source import Source

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubReleasesConnector(BaseConnector):
    """Fetch the latest releases from a GitHub repository."""

    async def fetch(
        self,
        source: Source,
        http_client: httpx.AsyncClient,
        db: AsyncSession,
    ) -> list[RawItemData]:
        owner_repo = _extract_owner_repo(source.source_url)
        if not owner_repo:
            logger.warning("Cannot parse GitHub owner/repo from %s", source.source_url)
            return []

        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        url = f"{GITHUB_API}/repos/{owner_repo}/releases"
        params = {"per_page": "10"}

        try:
            resp = await http_client.get(url, headers=headers, params=params, timeout=30)
        except httpx.HTTPError as exc:
            logger.warning("GitHub API failed for %s: %s", owner_repo, exc)
            return []

        if resp.status_code >= 400:
            logger.warning("GitHub API %s returned %d", owner_repo, resp.status_code)
            return []

        releases = resp.json()
        if not isinstance(releases, list):
            logger.warning("GitHub API %s unexpected response type", owner_repo)
            return []

        items: list[RawItemData] = []
        for rel in releases:
            published_str = rel.get("published_at") or rel.get("created_at")
            published_at = None
            if published_str:
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            items.append(
                RawItemData(
                    external_id=str(rel.get("id", "")),
                    url=rel.get("html_url", source.source_url),
                    title=rel.get("name") or rel.get("tag_name", ""),
                    content_text=rel.get("body", ""),
                    published_at=published_at,
                    metadata={
                        "tag_name": rel.get("tag_name"),
                        "prerelease": rel.get("prerelease", False),
                        "draft": rel.get("draft", False),
                    },
                )
            )

        logger.info("GitHub %s → %d releases", owner_repo, len(items))
        return items


def _extract_owner_repo(url: str) -> str | None:
    """Extract 'owner/repo' from a GitHub URL.

    Handles:
    - https://github.com/owner/repo/releases
    - https://github.com/owner/repo
    - https://github.com/owner  (org-level — not supported)
    """
    url = url.rstrip("/")
    if "/releases" in url:
        url = url.split("/releases")[0]

    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None
