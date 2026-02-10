"""Section allocation — route scored events into the 7 digest sections."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ai_digest.models.update_event import UpdateEvent
from ai_digest.taxonomy import (
    SECTION_DEVELOPER,
    SECTION_INCIDENTS,
    SECTION_MODELS,
    SECTION_PRICING,
    SECTION_QUOTAS,
)

logger = logging.getLogger(__name__)


@dataclass
class DigestSections:
    """Container for all 7 digest sections."""

    top5: list[UpdateEvent] = field(default_factory=list)
    developer: list[UpdateEvent] = field(default_factory=list)
    models: list[UpdateEvent] = field(default_factory=list)
    pricing: list[UpdateEvent] = field(default_factory=list)
    incidents: list[UpdateEvent] = field(default_factory=list)
    radar: list[UpdateEvent] = field(default_factory=list)
    everything_else: list[UpdateEvent] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return (
            len(self.top5)
            + len(self.developer)
            + len(self.models)
            + len(self.pricing)
            + len(self.incidents)
            + len(self.radar)
            + len(self.everything_else)
        )

    def to_dict(self) -> dict:
        """Serialise for storage in digests.sections JSONB column."""
        def event_ids(events: list[UpdateEvent]) -> list[str]:
            return [str(e.event_id) for e in events]

        return {
            "top5": event_ids(self.top5),
            "developer": event_ids(self.developer),
            "models": event_ids(self.models),
            "pricing": event_ids(self.pricing),
            "incidents": event_ids(self.incidents),
            "radar": event_ids(self.radar),
            "everything_else": event_ids(self.everything_else),
        }


def allocate_sections(events: list[UpdateEvent]) -> DigestSections:
    """Allocate events into 7 digest sections following PLAN.md Section 8.3.

    Events must be pre-sorted by impact_score DESC.
    """
    sections = DigestSections()

    if not events:
        return sections

    # Top 5: highest impact_score regardless of category
    sections.top5 = events[:SECTION_QUOTAS["top5"]]
    assigned_ids = {e.event_id for e in sections.top5}
    remaining = [e for e in events if e.event_id not in assigned_ids]

    # Route remaining events: community sources → radar first, then by category
    for event in remaining:
        cats = set(event.categories)

        # Community sources (trust_tier 4) always go to radar first
        if event.trust_tier == 4 and len(sections.radar) < SECTION_QUOTAS["radar"]:
            sections.radar.append(event)
            assigned_ids.add(event.event_id)
        elif cats & SECTION_DEVELOPER and len(sections.developer) < SECTION_QUOTAS["developer"]:
            sections.developer.append(event)
            assigned_ids.add(event.event_id)
        elif cats & SECTION_MODELS and len(sections.models) < SECTION_QUOTAS["models"]:
            sections.models.append(event)
            assigned_ids.add(event.event_id)
        elif cats & SECTION_PRICING and len(sections.pricing) < SECTION_QUOTAS["pricing"]:
            sections.pricing.append(event)
            assigned_ids.add(event.event_id)
        elif cats & SECTION_INCIDENTS and len(sections.incidents) < SECTION_QUOTAS["incidents"]:
            sections.incidents.append(event)
            assigned_ids.add(event.event_id)

    # Everything else: all remaining events not yet assigned
    sections.everything_else = [e for e in events if e.event_id not in assigned_ids]

    # Set digest_section on each event
    for e in sections.top5:
        e.digest_section = "top5"
    for e in sections.developer:
        e.digest_section = "developer"
    for e in sections.models:
        e.digest_section = "models"
    for e in sections.pricing:
        e.digest_section = "pricing"
    for e in sections.incidents:
        e.digest_section = "incidents"
    for e in sections.radar:
        e.digest_section = "radar"
    for e in sections.everything_else:
        e.digest_section = "everything_else"

    logger.info(
        "Allocated sections: top5=%d dev=%d models=%d pricing=%d "
        "incidents=%d radar=%d other=%d",
        len(sections.top5), len(sections.developer), len(sections.models),
        len(sections.pricing), len(sections.incidents), len(sections.radar),
        len(sections.everything_else),
    )

    return sections
