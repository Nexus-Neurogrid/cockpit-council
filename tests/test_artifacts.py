"""Tests for artifact parser."""

import pytest

from cockpit.artifacts.parser import ArtifactParser
from cockpit.artifacts.types import ParsedArtifact


@pytest.fixture
def parser():
    return ArtifactParser()


class TestArtifactParser:
    def test_parse_email(self, parser):
        text = '''Here's the email:

```email
{"to": "user@example.com", "subject": "Hello", "body": "Hi there"}
```
'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "email"
        assert artifacts[0].content["to"] == "user@example.com"

    def test_parse_task(self, parser):
        text = '''```task
{"title": "Implement auth", "priority": "high"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "task"
        assert artifacts[0].content["title"] == "Implement auth"

    def test_parse_multiple(self, parser):
        text = '''```email
{"to": "a@b.com", "subject": "Hi", "body": "Test"}
```

Some text in between.

```task
{"title": "Do thing"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 2
        assert artifacts[0].artifact_type == "email"
        assert artifacts[1].artifact_type == "task"

    def test_skip_unknown_type(self, parser):
        text = '''```python
print("hello")
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0

    def test_skip_invalid_json(self, parser):
        text = '''```email
not valid json
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0

    def test_skip_missing_required_fields(self, parser):
        text = '''```email
{"to": "a@b.com"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0  # Missing subject and body

    def test_parse_envelope_pattern(self, parser):
        text = '''```task
{"tasks": [{"title": "Task 1"}, {"title": "Task 2"}]}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 2

    def test_parse_list(self, parser):
        text = '''```task
[{"title": "Task A"}, {"title": "Task B"}]
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 2

    def test_register_custom_type(self, parser):
        parser.register_type(["pr", "pull_request"], "pull_request", ["title", "branch"])
        text = '''```pr
{"title": "Fix bug", "branch": "fix/auth"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "pull_request"

    def test_remove_from_text(self, parser):
        text = '''Some text before.

```email
{"to": "a@b.com", "subject": "Hi", "body": "Test"}
```

Some text after.'''
        cleaned = parser.remove_from_text(text)
        assert "```email" not in cleaned
        assert "Some text before." in cleaned
        assert "Some text after." in cleaned
