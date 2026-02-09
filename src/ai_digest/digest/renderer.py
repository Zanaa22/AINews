"""Jinja2 rendering for email and web digest templates."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ai_digest.digest.sections import DigestSections

logger = logging.getLogger(__name__)

# Resolve templates directory relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATES_DIR = _PROJECT_ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_email_digest(
    digest_date: date,
    overview: str,
    sections: DigestSections,
) -> str:
    """Render the email HTML digest."""
    template = _env.get_template("email/digest.html")
    return template.render(
        date=digest_date.strftime("%B %d, %Y"),
        overview=overview,
        sections=sections,
    )


def render_web_digest(
    digest_date: date,
    overview: str,
    sections: DigestSections,
) -> str:
    """Render the web HTML digest page."""
    template = _env.get_template("web/digest.html")
    return template.render(
        date=digest_date.strftime("%B %d, %Y"),
        date_iso=digest_date.isoformat(),
        overview=overview,
        sections=sections,
    )


def render_archive(
    digests: list[dict],
) -> str:
    """Render the archive listing page.

    ``digests`` is a list of dicts with keys: date, date_iso, event_count, url.
    """
    template = _env.get_template("web/archive.html")
    return template.render(digests=digests)
