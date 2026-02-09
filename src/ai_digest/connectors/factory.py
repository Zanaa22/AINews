"""Connector factory — maps fetch_method to the right connector class."""

from __future__ import annotations

from ai_digest.connectors.api_poll import APIPollConnector
from ai_digest.connectors.base import BaseConnector
from ai_digest.connectors.github_releases import GitHubReleasesConnector
from ai_digest.connectors.html_diff import HTMLDiffConnector
from ai_digest.connectors.rss import RSSConnector

_CONNECTOR_MAP: dict[str, type[BaseConnector]] = {
    "rss": RSSConnector,
    "html_diff": HTMLDiffConnector,
    "github_releases": GitHubReleasesConnector,
    "api_poll": APIPollConnector,
    "social_api": RSSConnector,  # Reddit RSS is handled by RSSConnector
}


def connector_for_source(fetch_method: str) -> BaseConnector:
    """Return an instantiated connector for the given fetch_method.

    Raises ValueError if the method is not supported.
    """
    cls = _CONNECTOR_MAP.get(fetch_method)
    if cls is None:
        raise ValueError(
            f"Unknown fetch_method {fetch_method!r}. "
            f"Supported: {', '.join(_CONNECTOR_MAP)}"
        )
    return cls()
