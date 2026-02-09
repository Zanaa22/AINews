"""Web publisher — save rendered digest as static HTML files."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from ai_digest.config import settings
from ai_digest.digest.renderer import render_archive

logger = logging.getLogger(__name__)


async def publish_web_digest(
    digest_date: date,
    web_html: str,
) -> str:
    """Write the rendered digest HTML to the web output directory.

    Returns the relative URL path for the published page.
    """
    output_dir = Path(settings.web_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"digest-{digest_date.isoformat()}.html"
    filepath = output_dir / filename
    filepath.write_text(web_html, encoding="utf-8")

    logger.info("Published web digest to %s", filepath)
    return f"/digests/{digest_date.isoformat()}"


async def rebuild_archive() -> None:
    """Rebuild the archive index page from existing digest files."""
    output_dir = Path(settings.web_output_dir)
    if not output_dir.exists():
        return

    digests = []
    for f in sorted(output_dir.glob("digest-*.html"), reverse=True):
        # Extract date from filename: digest-YYYY-MM-DD.html
        date_str = f.stem.replace("digest-", "")
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            continue
        digests.append({
            "date": d.strftime("%B %d, %Y"),
            "date_iso": d.isoformat(),
            "event_count": "—",  # would need DB to get actual count
            "url": f"/digests/{d.isoformat()}",
        })

    archive_html = render_archive(digests)
    (output_dir / "index.html").write_text(archive_html, encoding="utf-8")
    logger.info("Rebuilt archive index with %d digests", len(digests))
