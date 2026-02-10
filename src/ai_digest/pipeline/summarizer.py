"""LLM-powered grounded summarization using Anthropic Claude API."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.models.raw_item import RawItem
from ai_digest.models.update_event import UpdateEvent
from ai_digest.taxonomy import CATEGORY_NAMES

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_ALPHA_RE = re.compile(r"[A-Za-z]{2,}")

SYSTEM_PROMPT = """\
You are a factual AI news summarizer. Your job is to produce structured
summaries of AI industry updates. You MUST follow these rules:

1. NEVER invent facts. Every claim in "what_changed" MUST have a citation URL.
2. Separate facts (what_changed) from interpretation (why_it_matters).
3. If the source is first-party (Tier 1), you may say "released" or "updated."
   If only Tier 2/3/4 sources exist, say "reported" or "according to [source]."
4. Include at least one verbatim evidence snippet from the source material.
5. Tag with categories from this taxonomy: {categories}
6. Flag breaking_change = true only if the change removes existing functionality
   or requires developer action to avoid breakage.
7. Set confidence: "confirmed" if Tier 1, "likely" if Tier 2, "unverified" if Tier 3/4.
8. Keep title under 100 characters, action-oriented.
9. Keep why_it_matters to 1-2 sentences max.

OUTPUT FORMAT: JSON matching this schema exactly:
{{
  "title": "string — short action-oriented headline, <=100 chars",
  "what_changed": [
    {{
      "fact": "string — one factual statement",
      "citation_url": "string — URL backing this fact"
    }}
  ],
  "why_it_matters": "string — 1-2 sentences, interpretation/analysis",
  "action_items": ["string — optional concrete next steps"],
  "citations": ["url1", "url2"],
  "evidence_snippets": ["exact quote or data point from source"],
  "tags": {{
    "categories": ["category name from taxonomy"],
    "company": "string",
    "product_line": "string or null"
  }},
  "breaking_change": false,
  "confidence": "confirmed | likely | unverified",
  "severity_suggestion": "HIGH | MEDIUM | LOW"
}}
""".format(categories=", ".join(CATEGORY_NAMES))

USER_PROMPT_TEMPLATE = """\
Summarize the following source material about an AI industry update.

Source trust tier: {trust_tier}
Source company: {company}
Source URL: {url}
Published: {published}

--- SOURCE CONTENT START ---
{content}
--- SOURCE CONTENT END ---

{context_section}

Produce the JSON summary."""


async def summarize_event(
    event: UpdateEvent,
    client: anthropic.AsyncAnthropic,
    context_items: list[str] | None = None,
    raw_content: str | None = None,
) -> UpdateEvent:
    """Call Claude API to generate a grounded summary for an event.

    Populates: what_changed, why_it_matters, action_items, evidence_snippets,
    summary_short, summary_medium, and optionally adjusts severity/categories.
    """
    content = _build_content(event, raw_content)
    if not content:
        logger.warning("No content to summarize for event %s", event.title)
        return event

    context_section = ""
    if context_items:
        context_section = (
            "Additional context from other sources (if any):\n"
            + "\n".join(context_items)
        )

    user_prompt = USER_PROMPT_TEMPLATE.format(
        trust_tier=event.trust_tier,
        company=event.company_name,
        url=event.citations[0] if event.citations else "",
        published=str(event.published_at or ""),
        content=content[:4000],  # limit content to avoid token overflow
        context_section=context_section,
    )

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error for %s: %s", event.title, exc)
        _set_fallback_summary(event)
        return event

    # Parse LLM response
    raw_text = response.content[0].text
    parsed = _parse_llm_json(raw_text)

    if parsed:
        _apply_llm_output(event, parsed)
    else:
        logger.warning("Failed to parse LLM JSON for %s", event.title)
        _set_fallback_summary(event)

    return event


async def summarize_batch(
    events: list[UpdateEvent],
    client: anthropic.AsyncAnthropic,
    db: AsyncSession | None = None,
) -> list[UpdateEvent]:
    """Summarize a batch of events sequentially."""
    raw_map: dict[Any, str] = {}
    if db:
        raw_ids = [ev.raw_item_id for ev in events if ev.raw_item_id]
        if raw_ids:
            result = await db.execute(
                select(
                    RawItem.raw_item_id,
                    RawItem.content_text,
                    RawItem.content_html,
                    RawItem.title,
                ).where(RawItem.raw_item_id.in_(raw_ids))
            )
            for row in result:
                raw_map[row.raw_item_id] = (
                    row.content_text
                    or row.content_html
                    or row.title
                    or ""
                )
    for event in events:
        if event.summary_short:
            continue  # already summarized
        raw_content = getattr(event, "_raw_content", None) or raw_map.get(event.raw_item_id)
        await summarize_event(event, client, raw_content=raw_content)
    logger.info("Summarized %d events", len(events))
    return events


def _clean_content(text: str) -> str:
    clean = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", clean).strip()


def _is_readable(text: str, min_words: int = 3) -> bool:
    words = text.split()
    if len(words) < min_words:
        return False
    alpha_words = sum(1 for w in words if _ALPHA_RE.search(w))
    return alpha_words / len(words) > 0.3


def _build_content(event: UpdateEvent, raw_content: str | None = None) -> str:
    """Build the source content string for the LLM prompt."""
    parts = []
    if event.title:
        parts.append(f"Title: {event.title}")
    if raw_content:
        clean = _clean_content(raw_content)
        if clean and _is_readable(clean, min_words=1):
            parts.append(f"Content: {clean}")
    # Include any existing structured fields as extra context.
    if event.what_changed:
        for item in event.what_changed:
            if isinstance(item, dict):
                parts.append(item.get("fact", ""))
    if event.why_it_matters:
        parts.append(event.why_it_matters)
    return "\n".join(parts) if parts else event.title or ""


def _parse_llm_json(text: str) -> dict[str, Any] | None:
    """Try to extract JSON from LLM response text."""
    # Try direct parse
    text = text.strip()
    if text.startswith("```"):
        # Strip markdown code fence
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


def _apply_llm_output(event: UpdateEvent, data: dict[str, Any]) -> None:
    """Apply parsed LLM JSON output to the UpdateEvent."""
    if title := data.get("title"):
        event.title = title[:200]

    if what_changed := data.get("what_changed"):
        event.what_changed = what_changed

    if why := data.get("why_it_matters"):
        event.why_it_matters = why

    if actions := data.get("action_items"):
        event.action_items = actions

    if citations := data.get("citations"):
        event.citations = citations

    if snippets := data.get("evidence_snippets"):
        event.evidence_snippets = snippets

    if tags := data.get("tags"):
        if cats := tags.get("categories"):
            event.categories = cats
        if company := tags.get("company"):
            event.company_name = company
        if product := tags.get("product_line"):
            event.product_line = product

    if data.get("breaking_change"):
        event.breaking_change = True

    if confidence := data.get("confidence"):
        event.confidence = confidence

    if severity := data.get("severity_suggestion"):
        event.severity = severity

    # Generate short and medium summaries from the structured data
    what_facts = []
    if event.what_changed and isinstance(event.what_changed, list):
        what_facts = [
            item.get("fact", "") if isinstance(item, dict) else str(item)
            for item in event.what_changed
        ]

    event.summary_short = f"{event.title}. {event.why_it_matters or ''}"[:300]
    event.summary_medium = (
        f"{event.title}\n\n"
        + "\n".join(f"- {f}" for f in what_facts)
        + f"\n\n{event.why_it_matters or ''}"
    )[:1000]


def _set_fallback_summary(event: UpdateEvent) -> None:
    """Set minimal summary when LLM call fails."""
    event.summary_short = event.title[:300]
    event.summary_medium = event.title[:1000]
