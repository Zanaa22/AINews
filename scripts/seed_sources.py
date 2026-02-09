#!/usr/bin/env python3
"""Seed the source registry from CSV."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_digest.database import async_session_factory
from ai_digest.seed import seed_sources


async def main():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "sources_seed.csv"

    async with async_session_factory() as db:
        count = await seed_sources(db, csv_path)
        print(f"Seeded {count} sources from {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
