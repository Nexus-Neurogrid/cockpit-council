"""Embedded PostgreSQL lifecycle manager.

Provides zero-setup persistence: downloads and runs a PostgreSQL instance
in ``~/.cockpit/data/`` automatically.  Set ``COCKPIT_DATABASE_URL`` to
use an external Postgres instead.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

try:
    import psycopg
except ImportError:
    psycopg = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_COCKPIT_HOME = Path.home() / ".cockpit"
_DATA_DIR = _COCKPIT_HOME / "data"

_pg_server = None  # Module-level singleton
_cockpit_url: str | None = None  # Cached URL after first start


def get_connection_url() -> str:
    """Return the current database URL (does not start PG)."""
    external = os.environ.get("COCKPIT_DATABASE_URL")
    if external:
        return external
    if _cockpit_url:
        return _cockpit_url
    raise RuntimeError("Database not started. Run 'cockpit init' first.")


def _check_db_deps() -> None:
    if psycopg is None:
        raise ImportError(
            "Database features require the 'db' extra: "
            "pip install cockpit-council[db]"
        )


async def ensure_running() -> str:
    """Start the embedded PG if needed and return the connection URL.

    If ``COCKPIT_DATABASE_URL`` is set, returns that URL directly and
    does not start an embedded instance.
    """
    _check_db_deps()
    global _pg_server, _cockpit_url

    external = os.environ.get("COCKPIT_DATABASE_URL")
    if external:
        logger.info("Using external database: %s", external.split("@")[-1])
        return external

    if _pg_server is not None and _cockpit_url:
        return _cockpit_url

    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import pgserver

        _pg_server = pgserver.get_server(
            _DATA_DIR,
            cleanup_mode="stop",
        )
        base_url = _pg_server.get_uri()
        logger.info("Embedded PostgreSQL started: %s", base_url)

        # Create the cockpit database if it doesn't exist
        with psycopg.connect(base_url, autocommit=True) as conn:
            cur = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = 'cockpit'"
            )
            if cur.fetchone() is None:
                conn.execute("CREATE DATABASE cockpit")
                logger.info("Created 'cockpit' database")

        # Swap the default db name to 'cockpit' in the URI
        _cockpit_url = base_url.replace("/postgres?", "/cockpit?")
        return _cockpit_url

    except ImportError:
        raise RuntimeError(
            "pgserver is required for embedded PostgreSQL. "
            "Install it: pip install pgserver\n"
            "Or set COCKPIT_DATABASE_URL to use an external Postgres."
        )


async def get_connection():
    """Get an async psycopg connection to the cockpit database."""
    _check_db_deps()
    url = await ensure_running()
    conn = await psycopg.AsyncConnection.connect(url)
    return conn


async def stop():
    """Stop the embedded PostgreSQL if running."""
    global _pg_server, _cockpit_url
    if _pg_server is not None:
        _pg_server.cleanup()
        _pg_server = None
        _cockpit_url = None
        logger.info("Embedded PostgreSQL stopped")
