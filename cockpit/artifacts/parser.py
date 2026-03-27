"""Artifact parser — extracts structured artifacts from agent text output."""

from __future__ import annotations

import json
import logging
import re

from cockpit.artifacts.types import (
    DEFAULT_ARTIFACT_TYPES,
    DEFAULT_VALIDATORS,
    ParsedArtifact,
)

logger = logging.getLogger(__name__)

# Regex to find ```TYPE\n{json}\n``` blocks
_BLOCK_PATTERN = re.compile(
    r"```(\w+)\s*\n([\s\S]*?)```",
    re.MULTILINE,
)


class ArtifactParser:
    """Parse structured artifacts from agent text output.

    Looks for fenced code blocks with a type marker::

        ```email
        {"to": "user@example.com", "subject": "Hello", "body": "..."}
        ```

    The type marker is looked up in the type map to get the canonical
    artifact type name.
    """

    def __init__(
        self,
        type_map: dict[str, str] | None = None,
        validators: dict[str, list[str]] | None = None,
    ) -> None:
        self.type_map = dict(type_map or DEFAULT_ARTIFACT_TYPES)
        self.validators = dict(validators or DEFAULT_VALIDATORS)

    def register_type(
        self,
        markers: list[str],
        artifact_type: str,
        required_fields: list[str] | None = None,
    ) -> None:
        """Register a custom artifact type."""
        for marker in markers:
            self.type_map[marker.lower()] = artifact_type
        if required_fields:
            self.validators[artifact_type] = required_fields

    def parse(self, text: str) -> list[ParsedArtifact]:
        """Extract all artifacts from text."""
        artifacts: list[ParsedArtifact] = []

        for match in _BLOCK_PATTERN.finditer(text):
            marker = match.group(1).lower()
            raw_json = match.group(2).strip()

            artifact_type = self.type_map.get(marker)
            if not artifact_type:
                continue

            content = self._parse_json(raw_json)
            if content is None:
                continue

            # Handle list-wrapped content
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        artifacts.append(
                            ParsedArtifact(
                                artifact_type=artifact_type,
                                content=item,
                                raw_text=raw_json,
                                start_pos=match.start(),
                                end_pos=match.end(),
                            )
                        )
                continue

            # Handle envelope patterns: {"tasks": [...]}, {"artifacts": [...]}
            if isinstance(content, dict):
                for envelope_key in ("tasks", "artifacts", "items"):
                    if envelope_key in content and isinstance(content[envelope_key], list):
                        for item in content[envelope_key]:
                            if isinstance(item, dict):
                                artifacts.append(
                                    ParsedArtifact(
                                        artifact_type=artifact_type,
                                        content=item,
                                        raw_text=raw_json,
                                        start_pos=match.start(),
                                        end_pos=match.end(),
                                    )
                                )
                        break
                else:
                    # Validate required fields
                    if self._validate(artifact_type, content):
                        artifacts.append(
                            ParsedArtifact(
                                artifact_type=artifact_type,
                                content=content,
                                raw_text=raw_json,
                                start_pos=match.start(),
                                end_pos=match.end(),
                            )
                        )

        return artifacts

    def remove_from_text(self, text: str) -> str:
        """Remove all recognized artifact blocks from text."""
        result = text
        for match in reversed(list(_BLOCK_PATTERN.finditer(text))):
            marker = match.group(1).lower()
            if marker in self.type_map:
                result = result[: match.start()] + result[match.end() :]
        return result.strip()

    def _parse_json(self, raw: str) -> dict | list | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Failed to parse artifact JSON: %s...", raw[:100])
            return None

    def _validate(self, artifact_type: str, content: dict) -> bool:
        required = self.validators.get(artifact_type, [])
        for field in required:
            if field not in content:
                logger.debug(
                    "Artifact %s missing required field: %s", artifact_type, field
                )
                return False
        return True
