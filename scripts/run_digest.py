#!/usr/bin/env python3
"""Generate and optionally send today's digest (one-shot)."""

import argparse
import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_digest.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Generate today's AI digest")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        help="Digest date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send the digest via email after generation",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM summarization (use raw titles)",
    )
    args = parser.parse_args()

    import anthropic
    from ai_digest.database import async_session_factory
    from ai_digest.delivery.email_sender import send_digest_email
    from ai_digest.delivery.web_publisher import publish_web_digest, rebuild_archive
    from ai_digest.digest.generator import generate_digest

    anthropic_client = None
    if not args.no_llm and settings.anthropic_api_key:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async with async_session_factory() as db:
        logger.info("Generating digest for %s...", args.date)
        digest = await generate_digest(args.date, db, anthropic_client)

        if not digest:
            logger.warning("No events found — no digest generated")
            return

        logger.info("Digest generated: %d events", digest.event_count)

        # Publish web
        web_html = getattr(digest, "_web_html", None)
        if web_html:
            url = await publish_web_digest(args.date, web_html)
            logger.info("Published web digest: %s", url)

        # Send email
        if args.send_email:
            email_html = getattr(digest, "_email_html", None)
            if email_html:
                sent = await send_digest_email(args.date, email_html)
                if sent:
                    logger.info("Email sent successfully")
                else:
                    logger.warning("Email send failed")

    # Rebuild archive
    await rebuild_archive()
    logger.info("Done")


if __name__ == "__main__":
    asyncio.run(main())
