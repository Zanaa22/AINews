"""SQLAlchemy async engine, session factory, and declarative Base."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ai_digest.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Yield an async DB session (for use as FastAPI dependency)."""
    async with async_session_factory() as session:
        yield session
