"""Database models and query helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Deliberation(BaseModel):
    id: str
    query: str
    synthesis: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class Opinion(BaseModel):
    id: str
    deliberation_id: str
    agent: str
    content: str
    created_at: datetime | None = None


class Artifact(BaseModel):
    id: str
    deliberation_id: str | None = None
    artifact_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
    raw_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Memory(BaseModel):
    id: str
    agent_type: str
    key: str
    content: str
    memory_type: str = "fact"
    importance: float = 0.5
    created_at: datetime | None = None
    accessed_at: datetime | None = None
    access_count: int = 0


class Session(BaseModel):
    id: str
    agent: str
    messages: list[dict] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
