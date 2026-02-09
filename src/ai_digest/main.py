"""FastAPI application — entry point, routes, scheduler startup."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_digest.api.routes_digest import router as digest_router
from ai_digest.api.routes_health import router as health_router
from ai_digest.api.routes_sources import router as sources_router
from ai_digest.api.routes_web import router as web_router
from ai_digest.config import settings
from ai_digest.scheduler.jobs import schedule_fetch_jobs, setup_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — start scheduler, schedule fetch jobs."""
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    try:
        await schedule_fetch_jobs(scheduler)
    except Exception as exc:
        logger.warning("Could not schedule fetch jobs (DB may not be ready): %s", exc)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")


app = FastAPI(
    title="AI Daily Digest",
    description="Automated, citation-backed AI industry updates",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(web_router)
app.include_router(health_router)
app.include_router(digest_router)
app.include_router(sources_router)
