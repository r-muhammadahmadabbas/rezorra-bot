"""Async engine for Supabase Postgres.

The connection string comes ONLY from DATABASE_URL in .env - no credentials live
in code. If DATABASE_URL is unset the bot runs on the offline seed data instead
of failing, so local dev never hard-depends on the DB.

`statement_cache_size=0` is set because Supabase's transaction pooler (pgbouncer,
port 6543) does not support prepared statements. It is harmless on a direct
connection too.
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("rezorra.db")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

_engine = None
_session_factory = None


def is_configured() -> bool:
    return bool(DATABASE_URL)


def get_session_factory():
    """Lazily build the async engine + session factory. None if no DATABASE_URL."""
    global _engine, _session_factory
    if not DATABASE_URL:
        return None
    if _session_factory is None:
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args={"statement_cache_size": 0},
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        log.info("DB engine ready")
    return _session_factory
