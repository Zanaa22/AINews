"""Web UI routes — HTML pages for browsing the digest."""

from __future__ import annotations

from datetime import date, datetime, timezone
from html import escape as _esc
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.config import settings
from ai_digest.database import get_session
from ai_digest.models.digest import Digest
from ai_digest.models.raw_item import RawItem
from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent

router = APIRouter(tags=["web"])


def _page(title: str, body: str) -> str:
    """Wrap body HTML in the full page layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — AI Daily Digest</title>
  <style>
    :root {{
      --bg: #0f0f1a;
      --surface: #1a1a2e;
      --surface2: #222240;
      --primary: #6c63ff;
      --primary-light: #8b83ff;
      --accent: #00d4aa;
      --text: #e8e8f0;
      --text-muted: #8888a8;
      --border: #2a2a45;
      --high: #ff4757;
      --medium: #ffa502;
      --low: #2ed573;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
    }}
    a {{ color: var(--primary-light); text-decoration: none; }}
    a:hover {{ color: var(--accent); }}

    /* Nav */
    nav {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 16px 0;
      position: sticky; top: 0; z-index: 100;
    }}
    nav .inner {{
      max-width: 1100px; margin: 0 auto; padding: 0 24px;
      display: flex; justify-content: space-between; align-items: center;
    }}
    nav .logo {{ font-size: 20px; font-weight: 700; color: #fff; }}
    nav .logo span {{ color: var(--primary-light); }}
    nav .links a {{
      color: var(--text-muted); margin-left: 24px; font-size: 14px; font-weight: 500;
    }}
    nav .links a:hover {{ color: #fff; }}
    nav .links a.active {{ color: var(--primary-light); }}

    /* Container */
    .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}

    /* Hero */
    .hero {{
      text-align: center; padding: 60px 24px 40px;
    }}
    .hero h1 {{ font-size: 42px; font-weight: 800; margin-bottom: 12px; }}
    .hero h1 span {{ color: var(--primary-light); }}
    .hero p {{ font-size: 18px; color: var(--text-muted); max-width: 600px; margin: 0 auto 32px; }}
    .hero .cta {{
      display: inline-block; background: var(--primary); color: #fff;
      padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;
      transition: background 0.2s;
    }}
    .hero .cta:hover {{ background: var(--primary-light); color: #fff; }}

    /* Stats bar */
    .stats {{
      display: flex; gap: 24px; justify-content: center; flex-wrap: wrap;
      margin: 32px 0 48px;
    }}
    .stat {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 20px 32px; text-align: center; min-width: 160px;
    }}
    .stat .num {{ font-size: 32px; font-weight: 800; color: var(--primary-light); }}
    .stat .label {{ font-size: 13px; color: var(--text-muted); margin-top: 4px; }}

    /* Cards */
    .card {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 24px; margin-bottom: 16px;
      transition: border-color 0.2s;
    }}
    .card:hover {{ border-color: var(--primary); }}
    .card h3 {{ font-size: 18px; margin-bottom: 8px; }}
    .card .meta {{ font-size: 13px; color: var(--text-muted); }}
    .card-summary {{
      font-size: 13px; color: var(--text-muted); line-height: 1.5;
      margin-top: 10px; padding-top: 10px;
      border-top: 1px solid var(--border);
    }}
    .preview-list {{ margin-top: 10px; }}
    .preview-item {{
      font-size: 13px; color: var(--text);
      padding: 4px 0;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}

    /* Section titles */
    .section-title {{
      font-size: 13px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 2px; color: var(--primary-light);
      margin: 40px 0 20px; padding-bottom: 12px;
      border-bottom: 2px solid var(--border);
    }}

    /* Badges */
    .badge {{
      display: inline-block; font-size: 11px; font-weight: 700;
      padding: 3px 10px; border-radius: 4px; margin-right: 6px;
      vertical-align: middle;
    }}
    .badge-high {{ background: rgba(255,71,87,0.15); color: var(--high); }}
    .badge-medium {{ background: rgba(255,165,2,0.15); color: var(--medium); }}
    .badge-low {{ background: rgba(46,213,115,0.15); color: var(--low); }}
    .badge-cat {{ background: rgba(108,99,255,0.12); color: var(--primary-light); }}
    .badge-tier {{ background: rgba(0,212,170,0.12); color: var(--accent); }}

    /* Source table */
    .source-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
    .source-card {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 18px; transition: border-color 0.2s;
    }}
    .source-card:hover {{ border-color: var(--primary); }}
    .source-card .company {{ font-size: 12px; color: var(--accent); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
    .source-card .name {{ font-size: 16px; font-weight: 600; margin: 4px 0 8px; }}
    .source-card .details {{ font-size: 13px; color: var(--text-muted); }}

    /* ---------- Redesigned Event Cards ---------- */
    .event-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px 24px;
      margin-bottom: 14px;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .event-card:hover {{
      border-color: var(--primary);
      box-shadow: 0 2px 16px rgba(108,99,255,0.08);
    }}
    .event-card.severity-high {{ border-left: 4px solid var(--high); }}
    .event-card.severity-medium {{ border-left: 4px solid var(--medium); }}
    .event-card.severity-low {{ border-left: 4px solid var(--low); }}

    .event-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .event-header .event-title {{
      font-size: 17px;
      font-weight: 700;
      color: #fff;
      line-height: 1.4;
      flex: 1;
    }}
    .event-header .event-title .rank {{
      color: var(--primary-light);
      margin-right: 6px;
    }}
    .event-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 10px;
    }}
    .event-company-line {{
      font-size: 13px;
      color: var(--accent);
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .event-summary {{
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 14px;
      padding: 10px 14px;
      background: rgba(108,99,255,0.04);
      border-radius: 6px;
      border-left: 3px solid var(--primary);
      overflow: hidden;
      max-height: 4.5em;
    }}

    .event-body {{
      font-size: 14px;
      color: var(--text);
      line-height: 1.7;
    }}
    .event-body .label {{
      display: block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin: 14px 0 6px 0;
    }}
    .event-body .label:first-child {{ margin-top: 0; }}
    .event-body ul {{
      padding-left: 18px;
      margin: 4px 0 0 0;
    }}
    .event-body li {{
      margin-bottom: 5px;
      color: var(--text);
    }}
    .event-body li a {{
      font-size: 12px;
      color: var(--primary-light);
      margin-left: 4px;
    }}
    .event-body p {{
      margin: 4px 0 0 0;
      color: var(--text-muted);
    }}

    .event-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
    }}
    .event-footer a {{
      color: var(--primary-light);
      font-weight: 500;
    }}
    .event-footer a:hover {{ color: var(--accent); }}
    .event-source-links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .event-source-links a {{
      background: rgba(108,99,255,0.08);
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 12px;
      transition: background 0.2s;
    }}
    .event-source-links a:hover {{
      background: rgba(108,99,255,0.2);
    }}

    /* Compact events (everything else) */
    .compact-event {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      border-radius: 8px;
      margin-bottom: 4px;
      transition: background 0.15s;
    }}
    .compact-event:hover {{ background: var(--surface2); }}
    .compact-event .ce-content {{
      flex: 1;
      min-width: 0;
    }}
    .compact-event .ce-title {{
      font-size: 14px;
      font-weight: 500;
      display: block;
    }}
    .compact-event .ce-summary {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
      margin-top: 3px;
      overflow: hidden;
      max-height: 2.8em;
    }}
    .compact-event .ce-company {{
      font-size: 12px;
      color: var(--accent);
      min-width: 100px;
      flex-shrink: 0;
    }}

    /* Download button */
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 18px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s;
      cursor: pointer;
      border: none;
    }}
    .btn-outline {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-muted);
    }}
    .btn-outline:hover {{
      border-color: var(--primary-light);
      color: var(--primary-light);
      background: rgba(108,99,255,0.06);
    }}

    /* Footer */
    footer {{
      text-align: center; padding: 40px 24px;
      color: var(--text-muted); font-size: 13px;
      border-top: 1px solid var(--border); margin-top: 60px;
    }}
  </style>
</head>
<body>
  <nav>
    <div class="inner">
      <a href="/" class="logo">AI <span>Daily Digest</span></a>
      <div class="links">
        <a href="/">Home</a>
        <a href="/archive">Archive</a>
        <a href="/sources-ui">Sources</a>
        <a href="/health">API Health</a>
      </div>
    </div>
  </nav>
  {body}
  <footer>
    <p>AI Daily Digest &mdash; automated, citation-backed AI industry updates.</p>
  </footer>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def homepage(db: AsyncSession = Depends(get_session)):
    """Main dashboard / homepage."""
    source_count = await db.scalar(select(func.count(Source.source_id)))
    enabled_count = await db.scalar(
        select(func.count(Source.source_id)).where(Source.enabled.is_(True))
    )
    event_count = await db.scalar(select(func.count(UpdateEvent.event_id)))
    digest_count = await db.scalar(select(func.count(Digest.digest_id)))

    # Latest digest
    latest = await db.scalar(
        select(Digest.digest_date).order_by(Digest.digest_date.desc()).limit(1)
    )

    # Recent digests
    result = await db.execute(
        select(Digest).order_by(Digest.digest_date.desc()).limit(7)
    )
    digests = result.scalars().all()

    # Load top 3 events per digest for preview
    digest_ids = [d.digest_id for d in digests]
    top_events_by_digest: dict[str, list[UpdateEvent]] = {str(d.digest_id): [] for d in digests}
    if digest_ids:
        ev_result = await db.execute(
            select(UpdateEvent)
            .where(UpdateEvent.digest_id.in_(digest_ids))
            .order_by(UpdateEvent.impact_score.desc())
        )
        for ev in ev_result.scalars().all():
            bucket = top_events_by_digest.get(str(ev.digest_id), [])
            if len(bucket) < 3:
                bucket.append(ev)
                top_events_by_digest[str(ev.digest_id)] = bucket

    digest_cards = ""
    for d in digests:
        overview_snippet = ""
        if d.overview_text:
            text = d.overview_text[:180]
            if len(d.overview_text) > 180:
                text += "..."
            overview_snippet = f'<div class="card-summary">{_esc(text)}</div>'

        top_evs = top_events_by_digest.get(str(d.digest_id), [])
        preview_items = ""
        for ev in top_evs:
            sev_class = ev.severity.lower() if ev.severity else "low"
            preview_items += f'<div class="preview-item"><span class="badge badge-{sev_class}" style="font-size:10px;padding:2px 6px;">{ev.severity}</span> {_esc(ev.title)}</div>'

        digest_cards += f"""
        <a href="/view/{d.digest_date.isoformat()}" class="card" style="display:block;">
          <h3>{d.digest_date.strftime('%B %d, %Y')}</h3>
          <div class="meta">{d.event_count} items &middot; Generated {d.generated_at.strftime('%H:%M UTC') if d.generated_at else 'N/A'}</div>
          {overview_snippet}
          <div class="preview-list">{preview_items}</div>
        </a>"""

    if not digest_cards:
        digest_cards = '<p style="color:var(--text-muted);">No digests generated yet. Run <code>python scripts/run_digest.py</code></p>'

    body = f"""
    <div class="hero">
      <h1>AI <span>Daily Digest</span></h1>
      <p>Automated, citation-backed intelligence on what changed across AI companies and the builder community.</p>
      {"<a href='/view/" + latest.isoformat() + "' class='cta'>Read Today's Digest &rarr;</a>" if latest else "<span class='cta' style='opacity:0.5'>No digest yet</span>"}
    </div>

    <div class="stats">
      <div class="stat"><div class="num">{source_count}</div><div class="label">Sources</div></div>
      <div class="stat"><div class="num">{enabled_count}</div><div class="label">Active</div></div>
      <div class="stat"><div class="num">{event_count}</div><div class="label">Events</div></div>
      <div class="stat"><div class="num">{digest_count}</div><div class="label">Digests</div></div>
    </div>

    <div class="container">
      <div class="section-title">Recent Digests</div>
      {digest_cards}
    </div>
    """
    return HTMLResponse(_page("Home", body))


@router.get("/archive", response_class=HTMLResponse)
async def archive_page(db: AsyncSession = Depends(get_session)):
    """Digest archive page."""
    result = await db.execute(
        select(Digest).order_by(Digest.digest_date.desc()).limit(100)
    )
    digests = result.scalars().all()

    # Load top 3 events per digest for preview
    digest_ids = [d.digest_id for d in digests]
    top_events_by_digest: dict[str, list[UpdateEvent]] = {str(d.digest_id): [] for d in digests}
    if digest_ids:
        ev_result = await db.execute(
            select(UpdateEvent)
            .where(UpdateEvent.digest_id.in_(digest_ids))
            .order_by(UpdateEvent.impact_score.desc())
        )
        for ev in ev_result.scalars().all():
            bucket = top_events_by_digest.get(str(ev.digest_id), [])
            if len(bucket) < 3:
                bucket.append(ev)
                top_events_by_digest[str(ev.digest_id)] = bucket

    cards = ""
    for d in digests:
        overview_snippet = ""
        if d.overview_text:
            text = d.overview_text[:180]
            if len(d.overview_text) > 180:
                text += "..."
            overview_snippet = f'<div class="card-summary">{_esc(text)}</div>'

        top_evs = top_events_by_digest.get(str(d.digest_id), [])
        preview_items = ""
        for ev in top_evs:
            sev_class = ev.severity.lower() if ev.severity else "low"
            preview_items += f'<div class="preview-item"><span class="badge badge-{sev_class}" style="font-size:10px;padding:2px 6px;">{ev.severity}</span> {_esc(ev.title)}</div>'

        cards += f"""
        <a href="/view/{d.digest_date.isoformat()}" class="card" style="display:block;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>{d.digest_date.strftime('%B %d, %Y')}</h3>
            <span class="badge badge-cat">{d.event_count} items</span>
          </div>
          <div class="meta">
            Generated {d.generated_at.strftime('%H:%M UTC') if d.generated_at else 'N/A'}
            {' &middot; Delivered via ' + ', '.join(d.delivery_channels) if d.delivery_channels else ''}
          </div>
          {overview_snippet}
          <div class="preview-list">{preview_items}</div>
        </a>"""

    if not cards:
        cards = '<p style="color:var(--text-muted);">No digests yet.</p>'

    body = f"""
    <div class="container">
      <h2 style="margin-bottom: 8px;">Digest Archive</h2>
      <p style="color:var(--text-muted); margin-bottom: 32px;">All generated digests, newest first.</p>
      {cards}
    </div>"""
    return HTMLResponse(_page("Archive", body))


@router.get("/sources-ui", response_class=HTMLResponse)
async def sources_page(db: AsyncSession = Depends(get_session)):
    """Sources dashboard page."""
    result = await db.execute(
        select(Source).order_by(Source.company_slug, Source.source_name)
    )
    sources = result.scalars().all()

    cards = ""
    for s in sources:
        status_color = "var(--low)" if s.health_status == "healthy" else "var(--high)" if s.health_status == "dead" else "var(--medium)"
        last_fetch = s.last_fetched_at.strftime('%b %d, %H:%M') if s.last_fetched_at else "Never"
        cards += f"""
        <div class="source-card">
          <div class="company">{s.company_name}{(' / ' + s.product_line) if s.product_line else ''}</div>
          <div class="name">{s.source_name}</div>
          <div class="details">
            <span class="badge badge-tier">{s.fetch_method}</span>
            <span class="badge" style="background:rgba(0,212,170,0.12);color:var(--accent);">Tier {s.trust_tier}</span>
            <span class="badge" style="background:rgba(0,0,0,0.2);color:{status_color};">● {s.health_status}</span>
          </div>
          <div class="details" style="margin-top:8px;">
            Every {s.poll_frequency_min}min &middot; Priority: {s.priority} &middot; Last fetch: {last_fetch}
          </div>
        </div>"""

    body = f"""
    <div class="container">
      <h2 style="margin-bottom: 8px;">Source Registry</h2>
      <p style="color:var(--text-muted); margin-bottom: 32px;">{len(sources)} sources configured.</p>
      <div class="source-grid">{cards}</div>
    </div>"""
    return HTMLResponse(_page("Sources", body))


async def _load_digest_and_events(
    digest_date: date, db: AsyncSession
) -> tuple[Digest | None, list[UpdateEvent]]:
    """Shared helper to load a digest and its events."""
    stmt = select(Digest).where(Digest.digest_date == digest_date)
    result = await db.execute(stmt)
    digest = result.scalar_one_or_none()
    if not digest:
        return None, []
    events_result = await db.execute(
        select(UpdateEvent)
        .where(UpdateEvent.digest_id == digest.digest_id)
        .order_by(UpdateEvent.impact_score.desc())
    )
    events = list(events_result.scalars().all())

    # Backfill description from raw_items for events missing summaries
    needs_backfill = [
        ev for ev in events
        if not ev.summary_short and not ev.why_it_matters
    ]
    if needs_backfill:
        raw_ids = [ev.raw_item_id for ev in needs_backfill]
        raw_result = await db.execute(
            select(RawItem.raw_item_id, RawItem.content_text)
            .where(RawItem.raw_item_id.in_(raw_ids))
        )
        raw_texts = {row.raw_item_id: row.content_text for row in raw_result}
        for ev in needs_backfill:
            text = raw_texts.get(ev.raw_item_id)
            if text:
                # Clean up: take first sentence or first 150 chars
                clean = text.strip().replace("\n", " ").replace("\r", "")
                dot = clean.find(". ")
                if 20 < dot < 200:
                    clean = clean[:dot + 1]
                else:
                    clean = clean[:150]
                    if len(text.strip()) > 150:
                        clean += "..."
                ev.summary_short = clean

    return digest, events


def _group_events(events: list[UpdateEvent]) -> dict[str, list[UpdateEvent]]:
    """Group events by their digest section."""
    sections: dict[str, list[UpdateEvent]] = {
        "top5": [], "developer": [], "models": [],
        "pricing": [], "incidents": [], "radar": [], "everything_else": [],
    }
    for ev in events:
        sec = ev.digest_section or "everything_else"
        if sec in sections:
            sections[sec].append(ev)
        else:
            sections["everything_else"].append(ev)
    return sections


SECTION_LABELS = {
    "top5": "Top 5 — High Impact",
    "developer": "Developer Changes",
    "models": "Models & Capabilities",
    "pricing": "Pricing & Limits",
    "incidents": "Incidents & Reliability",
    "radar": "Community Radar",
    "everything_else": "Everything Else",
}


@router.get("/view/{digest_date}", response_class=HTMLResponse)
async def view_digest(
    digest_date: date,
    db: AsyncSession = Depends(get_session),
):
    """View a full digest with all events rendered."""
    digest, events = await _load_digest_and_events(digest_date, db)

    if not digest:
        return HTMLResponse(_page("Not Found", '<div class="container"><h2>Digest not found</h2><p><a href="/archive">Back to archive</a></p></div>'), status_code=404)

    sections = _group_events(events)

    def _extract_domain(url: str) -> str:
        """Extract a short domain label from a URL."""
        try:
            from urllib.parse import urlparse
            host = urlparse(url).netloc
            # Remove www. prefix
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return url[:30]

    def render_event(ev: UpdateEvent, numbered: int = 0) -> str:
        sev_class = ev.severity.lower() if ev.severity else "low"
        rank_html = f'<span class="rank">#{numbered}</span> ' if numbered else ""

        # Tags row
        tags = f'<span class="badge badge-{sev_class}">{ev.severity}</span>'
        for c in (ev.categories or [])[:3]:
            tags += f'<span class="badge badge-cat">{_esc(c)}</span>'
        if ev.breaking_change:
            tags += '<span class="badge badge-high">BREAKING</span>'

        # Summary text — try dedicated fields, fall back to first what_changed fact
        summary_text = _esc(ev.summary_short or ev.summary_medium or ev.why_it_matters or "")
        if not summary_text and ev.what_changed and isinstance(ev.what_changed, list):
            for item in ev.what_changed:
                if isinstance(item, dict) and item.get("fact"):
                    summary_text = _esc(item["fact"])
                    break
                elif isinstance(item, str) and item.strip():
                    summary_text = _esc(item)
                    break

        # What changed
        what_changed_html = ""
        if ev.what_changed and isinstance(ev.what_changed, list):
            items = ""
            for item in ev.what_changed:
                if isinstance(item, dict):
                    fact = _esc(item.get("fact", ""))
                    cite = item.get("citation_url", "")
                    cite_link = f' <a href="{_esc(cite)}" target="_blank">[src]</a>' if cite else ""
                    items += f"<li>{fact}{cite_link}</li>"
                else:
                    items += f"<li>{_esc(str(item))}</li>"
            what_changed_html = f'<span class="label">What changed</span><ul>{items}</ul>'

        # Why it matters
        why_html = ""
        if ev.why_it_matters:
            why_html = f'<span class="label">Why it matters</span><p>{_esc(ev.why_it_matters)}</p>'

        # Source links
        source_links = ""
        if ev.citations:
            links = "".join(
                f'<a href="{u}" target="_blank">{_extract_domain(u)}</a>'
                for u in ev.citations
            )
            source_links = f'<div class="event-source-links">{links}</div>'

        # Confidence + tier
        meta_right = f'{ev.confidence} &middot; Tier {ev.trust_tier}'
        if ev.published_at:
            meta_right = ev.published_at.strftime('%b %d, %H:%M') + " &middot; " + meta_right

        title = _esc(ev.title)
        company = _esc(ev.company_name or "")
        product = _esc(ev.product_line or "")

        return f"""
        <div class="event-card severity-{sev_class}">
          <div class="event-header">
            <div class="event-title">{rank_html}{title}</div>
          </div>
          <div class="event-tags">{tags}</div>
          <div class="event-company-line">{company}{(' / ' + product) if product else ''}</div>
          {"<div class='event-summary'>" + summary_text + "</div>" if summary_text else ""}
          <div class="event-body">{what_changed_html}{why_html}</div>
          <div class="event-footer">
            {source_links}
            <span>{meta_right}</span>
          </div>
        </div>"""

    def render_compact(ev: UpdateEvent) -> str:
        sev_class = ev.severity.lower() if ev.severity else "low"
        link = ""
        if ev.citations:
            link = f'<a href="{_esc(ev.citations[0])}" target="_blank">{_esc(_extract_domain(ev.citations[0]))}</a>'
        summary = _esc(ev.summary_short or ev.summary_medium or ev.why_it_matters or "")
        if not summary and ev.what_changed and isinstance(ev.what_changed, list):
            for item in ev.what_changed:
                if isinstance(item, dict) and item.get("fact"):
                    summary = _esc(item["fact"])
                    break
                elif isinstance(item, str) and item.strip():
                    summary = _esc(item)
                    break
        summary_html = f'<div class="ce-summary">{summary}</div>' if summary else ""
        return f"""
        <div class="compact-event">
          <span class="badge badge-{sev_class}" style="flex-shrink:0;">{ev.severity}</span>
          <span class="ce-company">{_esc(ev.company_name or "")}</span>
          <div class="ce-content">
            <span class="ce-title">{_esc(ev.title)}</span>
            {summary_html}
          </div>
          {link}
        </div>"""

    # Build sections HTML
    content = ""
    section_order = ["top5", "developer", "models", "pricing", "incidents", "radar", "everything_else"]

    for idx, sec_key in enumerate(section_order, 1):
        if not sections[sec_key]:
            continue
        label = f"[{idx}] {SECTION_LABELS[sec_key]}"
        if sec_key == "everything_else":
            items = "".join(render_compact(ev) for ev in sections[sec_key])
            content += f'<div class="section-title">{label}</div><div class="card">{items}</div>'
        elif sec_key == "top5":
            items = "".join(render_event(ev, i + 1) for i, ev in enumerate(sections[sec_key]))
            content += f'<div class="section-title">{label}</div>{items}'
        else:
            items = "".join(render_event(ev) for ev in sections[sec_key])
            content += f'<div class="section-title">{label}</div>{items}'

    # Severity summary counts
    high_ct = sum(1 for ev in events if ev.severity == "HIGH")
    med_ct = sum(1 for ev in events if ev.severity == "MEDIUM")
    low_ct = sum(1 for ev in events if ev.severity == "LOW")

    body = f"""
    <div class="container">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px; margin-bottom: 32px;">
        <div>
          <a href="/archive" style="font-size:13px;">&larr; Back to Archive</a>
          <h2 style="margin-top:12px;">{digest_date.strftime('%B %d, %Y')}</h2>
          <p style="color:var(--text-muted); margin-top:4px;">
            {digest.event_count} items &middot;
            <span class="badge badge-high">{high_ct} High</span>
            <span class="badge badge-medium">{med_ct} Medium</span>
            <span class="badge badge-low">{low_ct} Low</span>
            &middot; Generated {digest.generated_at.strftime('%H:%M UTC') if digest.generated_at else ''}
          </p>
        </div>
        <a href="/view/{digest_date.isoformat()}/download" class="btn btn-outline" download>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Log
        </a>
      </div>
      {"<div class='card' style='border-left:3px solid var(--primary);'><p>" + _esc(digest.overview_text) + "</p></div>" if digest.overview_text else ""}
      {content}
    </div>"""

    return HTMLResponse(_page(digest_date.strftime('%B %d, %Y'), body))


@router.get("/view/{digest_date}/download")
async def download_digest_log(
    digest_date: date,
    db: AsyncSession = Depends(get_session),
):
    """Generate and return a downloadable Markdown log of the digest."""
    digest, events = await _load_digest_and_events(digest_date, db)

    if not digest:
        return PlainTextResponse("Digest not found.", status_code=404)

    sections = _group_events(events)

    lines: list[str] = []
    lines.append(f"# AI Daily Digest — {digest_date.strftime('%B %d, %Y')}")
    lines.append(f"Generated: {digest.generated_at.strftime('%Y-%m-%d %H:%M UTC') if digest.generated_at else 'N/A'}")
    lines.append(f"Total items: {digest.event_count}")
    lines.append("")

    if digest.overview_text:
        lines.append("## Overview")
        lines.append(digest.overview_text)
        lines.append("")

    section_order = ["top5", "developer", "models", "pricing", "incidents", "radar", "everything_else"]

    for idx, sec_key in enumerate(section_order, 1):
        if not sections[sec_key]:
            continue
        lines.append(f"## [{idx}] {SECTION_LABELS[sec_key]}")
        lines.append("")

        for i, ev in enumerate(sections[sec_key], 1):
            prefix = f"{i}. " if sec_key == "top5" else "- "
            lines.append(f"{prefix}**{ev.title}**")
            lines.append(f"  Company: {ev.company_name}{(' / ' + ev.product_line) if ev.product_line else ''}")
            lines.append(f"  Severity: {ev.severity} | Score: {ev.impact_score:.1f} | Confidence: {ev.confidence}")
            if ev.categories:
                lines.append(f"  Categories: {', '.join(ev.categories)}")

            if ev.what_changed and isinstance(ev.what_changed, list):
                lines.append("  What changed:")
                for item in ev.what_changed:
                    if isinstance(item, dict):
                        fact = item.get("fact", "")
                        cite = item.get("citation_url", "")
                        cite_str = f" ({cite})" if cite else ""
                        lines.append(f"    - {fact}{cite_str}")
                    else:
                        lines.append(f"    - {item}")

            if ev.why_it_matters:
                lines.append(f"  Why it matters: {ev.why_it_matters}")

            if ev.citations:
                lines.append(f"  Sources: {', '.join(ev.citations)}")

            lines.append("")

    lines.append("---")
    lines.append("AI Daily Digest — automated, citation-backed AI industry updates.")

    content = "\n".join(lines)
    filename = f"ai-digest-{digest_date.isoformat()}.md"

    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
