"""Memory store — PG-backed agent memory with semantic search."""

from __future__ import annotations

import logging
import uuid

try:
    import psycopg
except ImportError:
    psycopg = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class MemoryStore:
    """PostgreSQL-backed memory store with optional pgvector semantic search.

    Falls back to keyword-based search when no embedding function is provided.
    """

    def __init__(
        self,
        connection_url: str,
        embedding_fn=None,
    ) -> None:
        self._url = connection_url
        self._embed = embedding_fn  # async fn: str -> list[float]

    async def store(
        self,
        agent_type: str,
        key: str,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5,
    ) -> None:
        """Store or update a memory.  Upserts on (agent_type, key)."""
        embedding = None
        if self._embed:
            try:
                embedding = await self._embed(content)
            except Exception:
                logger.debug("Embedding generation failed, storing without vector")

        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            if embedding:
                sql = (
                    "INSERT INTO memories"
                    " (id, agent_type, key, content, memory_type, importance, embedding)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (agent_type, key)"
                    " DO UPDATE SET content = EXCLUDED.content,"
                    " memory_type = EXCLUDED.memory_type,"
                    " importance = EXCLUDED.importance,"
                    " embedding = EXCLUDED.embedding,"
                    " accessed_at = now()"
                )
                params = (
                    str(uuid.uuid4()), agent_type, key,
                    content, memory_type, importance, str(embedding),
                )
                await conn.execute(sql, params)
            else:
                await conn.execute(
                    """INSERT INTO memories (id, agent_type, key, content, memory_type, importance)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (agent_type, key)
                       DO UPDATE SET content = EXCLUDED.content,
                                     memory_type = EXCLUDED.memory_type,
                                     importance = EXCLUDED.importance,
                                     accessed_at = now()""",
                    (str(uuid.uuid4()), agent_type, key, content, memory_type, importance),
                )
            await conn.commit()

    async def recall(self, agent_type: str, key: str) -> dict | None:
        """Retrieve a specific memory by key.  Updates access stats."""
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                """UPDATE memories SET accessed_at = now(), access_count = access_count + 1
                   WHERE agent_type = %s AND key = %s
                   RETURNING *""",
                (agent_type, key),
            )
            row = await cur.fetchone()
            await conn.commit()
            if row is None:
                return None
            cols = [desc.name for desc in cur.description]
            return dict(zip(cols, row))

    async def search(
        self,
        query: str,
        agent_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search memories — vector similarity if available, else keyword."""
        if self._embed:
            return await self._vector_search(query, agent_type, limit)
        return await self._keyword_search(query, agent_type, limit)

    async def get_agent_context(self, agent_type: str) -> dict:
        """Return grouped memories for an agent (decisions, learnings, preferences, facts)."""
        result: dict[str, list[dict]] = {
            "decisions": [],
            "learnings": [],
            "preferences": [],
            "facts": [],
        }
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                """SELECT * FROM memories
                   WHERE agent_type = %s
                   ORDER BY importance DESC, accessed_at DESC
                   LIMIT 50""",
                (agent_type,),
            )
            rows = await cur.fetchall()
            cols = [desc.name for desc in cur.description]

            for row in rows:
                item = dict(zip(cols, row))
                mem_type = item.get("memory_type", "fact")
                bucket = mem_type + "s" if not mem_type.endswith("s") else mem_type
                if bucket in result:
                    result[bucket].append(item)
                else:
                    result["facts"].append(item)

        return result

    async def decay(self, days_threshold: int = 30, decay_factor: float = 0.9) -> int:
        """Reduce importance of old, unused memories.  Returns count affected."""
        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                """UPDATE memories
                   SET importance = importance * %s
                   WHERE accessed_at < now() - interval '%s days'
                     AND importance > 0.1
                   RETURNING id""",
                (decay_factor, days_threshold),
            )
            rows = await cur.fetchall()
            await conn.commit()
            return len(rows)

    # ------------------------------------------------------------------
    # Internal search implementations
    # ------------------------------------------------------------------

    async def _vector_search(
        self, query: str, agent_type: str | None, limit: int
    ) -> list[dict]:
        embedding = await self._embed(query)
        agent_filter = "AND agent_type = %s" if agent_type else ""
        params = [str(embedding), limit]
        if agent_type:
            params = [str(embedding), agent_type, limit]

        sql = f"""SELECT *, embedding <=> %s::vector AS distance
                  FROM memories
                  WHERE embedding IS NOT NULL {agent_filter}
                  ORDER BY distance ASC
                  LIMIT %s"""

        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(sql, params)
            rows = await cur.fetchall()
            cols = [desc.name for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]

    async def _keyword_search(
        self, query: str, agent_type: str | None, limit: int
    ) -> list[dict]:
        words = query.lower().split()
        if not words:
            return []

        conditions = ["LOWER(content) LIKE %s" for _ in words]
        params = [f"%{w}%" for w in words]

        if agent_type:
            conditions.append("agent_type = %s")
            params.append(agent_type)

        params.append(limit)
        where = " AND ".join(conditions)

        async with await psycopg.AsyncConnection.connect(self._url) as conn:
            cur = await conn.execute(
                f"""SELECT * FROM memories
                    WHERE {where}
                    ORDER BY importance DESC
                    LIMIT %s""",
                params,
            )
            rows = await cur.fetchall()
            cols = [desc.name for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
