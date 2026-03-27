"""Database schema initialization."""

from __future__ import annotations

import logging

import psycopg

logger = logging.getLogger(__name__)

SCHEMA_SQL = """\
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Deliberations (one per council run)
CREATE TABLE IF NOT EXISTS deliberations (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    query           TEXT NOT NULL,
    synthesis       TEXT,
    context         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Agent opinions (many per deliberation)
CREATE TABLE IF NOT EXISTS opinions (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    deliberation_id TEXT NOT NULL REFERENCES deliberations(id) ON DELETE CASCADE,
    agent           TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_opinions_deliberation ON opinions(deliberation_id);

-- Artifacts parsed from agent output
CREATE TABLE IF NOT EXISTS artifacts (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    deliberation_id TEXT REFERENCES deliberations(id) ON DELETE SET NULL,
    artifact_type   TEXT NOT NULL,
    content         JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'draft',
    raw_text        TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_artifacts_deliberation ON artifacts(deliberation_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);

-- Agent memories with vector embeddings
CREATE TABLE IF NOT EXISTS memories (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_type      TEXT NOT NULL,
    key             TEXT NOT NULL,
    content         TEXT NOT NULL,
    memory_type     TEXT NOT NULL DEFAULT 'fact',
    importance      REAL NOT NULL DEFAULT 0.5,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT now(),
    accessed_at     TIMESTAMPTZ DEFAULT now(),
    access_count    INTEGER DEFAULT 0,
    UNIQUE(agent_type, key)
);
CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_type);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);

-- Sessions (for office-style conversations)
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent           TEXT NOT NULL,
    messages        JSONB DEFAULT '[]',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
"""


async def run_migrations(connection_url: str) -> None:
    """Create all tables if they don't exist."""
    async with await psycopg.AsyncConnection.connect(connection_url) as conn:
        async with conn.cursor() as cur:
            await cur.execute(SCHEMA_SQL)
        await conn.commit()
    logger.info("Database migrations completed")
