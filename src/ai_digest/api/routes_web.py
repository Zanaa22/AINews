"""Web UI routes — HTML pages for browsing the digest."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_digest.config import settings
from ai_digest.database import get_session
from ai_digest.models.digest import Digest
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

    /* Event items */
    .event {{
      padding: 20px 0; border-bottom: 1px solid var(--border);
    }}
    .event:last-child {{ border-bottom: none; }}
    .event-title {{ font-size: 16px; font-weight: 600; margin-bottom: 6px; }}
    .event-company {{ font-size: 13px; color: var(--accent); margin-bottom: 8px; }}
    .event-body {{ font-size: 14px; color: var(--text-muted); }}
    .event-body ul {{ padding-left: 20px; margin: 6px 0; }}
    .event-body li {{ margin-bottom: 4px; color: var(--text); }}
    .event-sources {{ font-size: 12px; color: var(--text-muted); margin-top: 8px; }}

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

    digest_cards = ""
    for d in digests:
        digest_cards += f"""
        <a href="/view/{d.digest_date.isoformat()}" class="card" style="display:block;">
          <h3>{d.digest_date.strftime('%B %d, %Y')}</h3>
          <div class="meta">{d.event_count} items &middot; Generated {d.generated_at.strftime('%H:%M UTC') if d.generated_at else 'N/A'}</div>
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

    cards = ""
    for d in digests:
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


@router.get("/view/{digest_date}", response_class=HTMLResponse)
async def view_digest(
    digest_date: date,
    db: AsyncSession = Depends(get_session),
):
    """View a full digest with all events rendered."""
    stmt = select(Digest).where(Digest.digest_date == digest_date)
    result = await db.execute(stmt)
    digest = result.scalar_one_or_none()

    if not digest:
        return HTMLResponse(_page("Not Found", '<div class="container"><h2>Digest not found</h2><p><a href="/archive">Back to archive</a></p></div>'), status_code=404)

    # Get all events for this digest
    events_result = await db.execute(
        select(UpdateEvent)
        .where(UpdateEvent.digest_id == digest.digest_id)
        .order_by(UpdateEvent.impact_score.desc())
    )
    events = list(events_result.scalars().all())

    # Group by section
    sections: dict[str, list] = {
        "top5": [], "developer": [], "models": [],
        "pricing": [], "incidents": [], "radar": [], "everything_else": [],
    }
    for ev in events:
        sec = ev.digest_section or "everything_else"
        if sec in sections:
            sections[sec].append(ev)
        else:
            sections["everything_else"].append(ev)

    def render_event(ev: UpdateEvent, numbered: int = 0) -> str:
        prefix = f"{numbered}. " if numbered else ""
        sev_class = ev.severity.lower() if ev.severity else "low"
        cats = "".join(f'<span class="badge badge-cat">{c}</span>' for c in (ev.categories or [])[:2])

        what_changed_html = ""
        if ev.what_changed and isinstance(ev.what_changed, list):
            items = ""
            for item in ev.what_changed:
                if isinstance(item, dict):
                    fact = item.get("fact", "")
                    cite = item.get("citation_url", "")
                    cite_link = f' <a href="{cite}">[source]</a>' if cite else ""
                    items += f"<li>{fact}{cite_link}</li>"
                else:
                    items += f"<li>{item}</li>"
            what_changed_html = f"<strong>What changed:</strong><ul>{items}</ul>"

        why_html = f"<p><strong>Why it matters:</strong> {ev.why_it_matters}</p>" if ev.why_it_matters else ""
        sources_html = ""
        if ev.citations:
            links = ", ".join(f'<a href="{u}">{u[:50]}...</a>' if len(u) > 50 else f'<a href="{u}">{u}</a>' for u in ev.citations)
            sources_html = f'<div class="event-sources">Sources: {links} &middot; {ev.confidence} &middot; Tier {ev.trust_tier}</div>'

        return f"""
        <div class="event">
          <div class="event-title">{prefix}{ev.title}</div>
          <div><span class="badge badge-{sev_class}">{ev.severity}</span>{cats}</div>
          <div class="event-company">{ev.company_name}{(' / ' + ev.product_line) if ev.product_line else ''}</div>
          <div class="event-body">{what_changed_html}{why_html}</div>
          {sources_html}
        </div>"""

    def render_compact(ev: UpdateEvent) -> str:
        sev_class = ev.severity.lower() if ev.severity else "low"
        link = f'<a href="{ev.citations[0]}">[source]</a>' if ev.citations else ""
        return f'<div style="padding:6px 0;font-size:14px;">&#8226; {ev.title} <span class="badge badge-{sev_class}">{ev.severity}</span> {link}</div>'

    # Build sections HTML
    content = ""

    if sections["top5"]:
        items = "".join(render_event(ev, i + 1) for i, ev in enumerate(sections["top5"]))
        content += f'<div class="section-title">[1] Top 5 — High Impact</div><div class="card">{items}</div>'

    if sections["developer"]:
        items = "".join(render_event(ev) for ev in sections["developer"])
        content += f'<div class="section-title">[2] Developer Changes</div><div class="card">{items}</div>'

    if sections["models"]:
        items = "".join(render_event(ev) for ev in sections["models"])
        content += f'<div class="section-title">[3] Models &amp; Capabilities</div><div class="card">{items}</div>'

    if sections["pricing"]:
        items = "".join(render_event(ev) for ev in sections["pricing"])
        content += f'<div class="section-title">[4] Pricing &amp; Limits</div><div class="card">{items}</div>'

    if sections["incidents"]:
        items = "".join(render_event(ev) for ev in sections["incidents"])
        content += f'<div class="section-title">[5] Incidents &amp; Reliability</div><div class="card">{items}</div>'

    if sections["radar"]:
        items = "".join(render_event(ev) for ev in sections["radar"])
        content += f'<div class="section-title">[6] Community Radar</div><div class="card">{items}</div>'

    if sections["everything_else"]:
        items = "".join(render_compact(ev) for ev in sections["everything_else"])
        content += f'<div class="section-title">[7] Everything Else</div><div class="card">{items}</div>'

    body = f"""
    <div class="container">
      <div style="margin-bottom: 32px;">
        <a href="/archive" style="font-size:13px;">&larr; Back to Archive</a>
        <h2 style="margin-top:12px;">{digest_date.strftime('%B %d, %Y')}</h2>
        <p style="color:var(--text-muted);">{digest.event_count} items &middot; Generated {digest.generated_at.strftime('%H:%M UTC') if digest.generated_at else ''}</p>
      </div>
      {"<div class='card' style='border-left:3px solid var(--primary);'><p>" + digest.overview_text + "</p></div>" if digest.overview_text else ""}
      {content}
    </div>"""

    return HTMLResponse(_page(digest_date.strftime('%B %d, %Y'), body))
