"""Artifact store — DB-backed persistence for parsed artifacts."""

from __future__ import annotations

import json
import uuid

try:
    import psycopg
except ImportError:
    psycopg = None  # type: ignore[assignment]

from cockpit.artifacts.types import ParsedArtifact


class ArtifactStore:
    """Persist and query artifacts in PostgreSQL."""

    def __init__(self, connection_url: str) -> None:
        self._url = connection_url

    async def save(
        self,
        deliberation_id: str | None,
        artifacts: list[ParsedArtifact],
    ) -> list[str]:
        """Save parsed artifacts to the database.  Returns a list of IDs."""
        ids: list[str] = []
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            for artifact in artifacts:
                aid = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO artifacts (id, deliberation_id, artifact_type, content, raw_text)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        aid,
                        deliberation_id,
                        artifact.artifact_type,
                        json.dumps(artifact.content),
                        artifact.raw_text,
                    ),
                )
                ids.append(aid)
            await conn.commit()
        return ids

    async def get(self, artifact_id: str) -> dict | None:
        """Retrieve a single artifact by ID."""
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                "SELECT * FROM artifacts WHERE id = %s", (artifact_id,)
            )
            row = await cur.fetchone()
            if row is None:
                return None
            cols = [desc.name for desc in cur.description]
            return dict(zip(cols, row))

    async def list(
        self,
        deliberation_id: str | None = None,
        artifact_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query artifacts with optional filters."""
        conditions: list[str] = []
        params: list = []

        if deliberation_id:
            conditions.append("deliberation_id = %s")
            params.append(deliberation_id)
        if artifact_type:
            conditions.append("artifact_type = %s")
            params.append(artifact_type)
        if status:
            conditions.append("status = %s")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                f"SELECT * FROM artifacts {where} ORDER BY created_at DESC LIMIT %s",
                params,
            )
            rows = await cur.fetchall()
            cols = [desc.name for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]

    async def update_status(self, artifact_id: str, status: str) -> None:
        """Update an artifact's status (draft → pending → executed/cancelled)."""
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            await conn.execute(
                "UPDATE artifacts SET status = %s, updated_at = now() WHERE id = %s",
                (status, artifact_id),
            )
            await conn.commit()
