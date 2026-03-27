"""Artifact type definitions and registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Default artifact type markers → canonical type names.
# Keys are the markers found in ```[MARKER] code blocks.
DEFAULT_ARTIFACT_TYPES: dict[str, str] = {
    "email": "email",
    "calendar": "calendar_event",
    "calendar_event": "calendar_event",
    "task": "task",
    "document": "document",
    "code": "code",
    "brand_bible": "brand_bible",
    "wireframe": "wireframe",
    "estimate": "estimate",
    "proposal": "proposal",
    "audit": "audit_report",
    "linkedin_message": "linkedin_message",
    "linkedin_post": "linkedin_post",
    "x_post": "x_post",
}

# Required fields per artifact type (for validation).
DEFAULT_VALIDATORS: dict[str, list[str]] = {
    "email": ["to", "subject", "body"],
    "calendar_event": ["title", "date"],
    "task": ["title"],
    "document": ["title", "content"],
    "estimate": ["total"],
}


@dataclass
class ParsedArtifact:
    """An artifact parsed from agent output."""

    artifact_type: str
    content: dict[str, Any]
    raw_text: str
    start_pos: int = 0
    end_pos: int = 0
