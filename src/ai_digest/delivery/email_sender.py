"""Email delivery — Resend API primary, SMTP fallback."""

from __future__ import annotations

import logging
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import resend

from ai_digest.config import settings

logger = logging.getLogger(__name__)


async def send_digest_email(
    digest_date: date,
    html_content: str,
    recipients: list[str] | None = None,
) -> bool:
    """Send the digest email to all recipients.

    Uses Resend API if configured, falls back to SMTP.
    Returns True if at least one delivery succeeded.
    """
    to_addrs = recipients or settings.email_recipients
    if not to_addrs:
        logger.warning("No email recipients configured, skipping send")
        return False

    subject = f"AI Daily Digest — {digest_date.strftime('%B %d, %Y')}"

    if settings.resend_api_key:
        return await _send_via_resend(subject, html_content, to_addrs)
    elif settings.smtp_host and settings.smtp_user:
        return await _send_via_smtp(subject, html_content, to_addrs)
    else:
        logger.warning("No email provider configured (set RESEND_API_KEY or SMTP_*)")
        return False


async def _send_via_resend(
    subject: str,
    html: str,
    to_addrs: list[str],
) -> bool:
    """Send email via Resend API."""
    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": settings.digest_email_from,
                "to": to_addrs,
                "subject": subject,
                "html": html,
            }
        )
        logger.info("Email sent via Resend to %d recipients", len(to_addrs))
        return True
    except Exception as exc:
        logger.error("Resend send failed: %s", exc)
        return False


async def _send_via_smtp(
    subject: str,
    html: str,
    to_addrs: list[str],
) -> bool:
    """Send email via SMTP as fallback."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.digest_email_from
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
        )
        logger.info("Email sent via SMTP to %d recipients", len(to_addrs))
        return True
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return False
