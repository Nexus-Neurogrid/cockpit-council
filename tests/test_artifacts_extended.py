"""Extended artifact parser tests — edge cases and robustness."""

import pytest

from cockpit.artifacts.parser import ArtifactParser


@pytest.fixture
def parser():
    return ArtifactParser()


class TestArtifactEdgeCases:
    def test_nested_json_object(self, parser):
        text = '''```task
{"title": "Deploy", "metadata": {"env": "prod", "region": "eu-west-1"}, "tags": ["urgent", "ops"]}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].content["metadata"]["region"] == "eu-west-1"
        assert artifacts[0].content["tags"] == ["urgent", "ops"]

    def test_json_with_special_characters(self, parser):
        text = '''```email
{"to": "user@example.com", "subject": "Hello \\"World\\"", "body": "Line 1\\nLine 2"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert '"World"' in artifacts[0].content["subject"]

    def test_empty_json_object(self, parser):
        text = '''```task
{}
```'''
        # Task requires "title" field — should be rejected
        artifacts = parser.parse(text)
        assert len(artifacts) == 0

    def test_json_with_null_values(self, parser):
        text = '''```task
{"title": "Task with nulls", "description": null, "priority": null}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].content["title"] == "Task with nulls"

    def test_multiple_same_type(self, parser):
        text = '''```task
{"title": "Task 1"}
```
Some text.
```task
{"title": "Task 2"}
```
More text.
```task
{"title": "Task 3"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 3
        titles = [a.content["title"] for a in artifacts]
        assert titles == ["Task 1", "Task 2", "Task 3"]

    def test_mixed_types(self, parser):
        text = '''```email
{"to": "a@b.com", "subject": "Hi", "body": "Hello"}
```
```task
{"title": "Follow up"}
```
```code
{"language": "python", "content": "print('hello')"}
```'''
        artifacts = parser.parse(text)
        types = [a.artifact_type for a in artifacts]
        assert "email" in types
        assert "task" in types
        assert "code" in types

    def test_code_block_without_type_ignored(self, parser):
        text = '''```
Just a plain code block with no type marker
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0

    def test_malformed_json_with_trailing_comma(self, parser):
        text = '''```task
{"title": "Bad JSON",}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0

    def test_json_array_at_root(self, parser):
        text = '''```task
[{"title": "A"}, {"title": "B"}, {"title": "C"}]
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 3

    def test_envelope_with_artifacts_key(self, parser):
        text = '''```email
{"artifacts": [
    {"to": "a@b.com", "subject": "One", "body": "x"},
    {"to": "c@d.com", "subject": "Two", "body": "y"}
]}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 2

    def test_whitespace_around_json(self, parser):
        text = '''```task

    {"title": "Whitespace test"}

```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1

    def test_large_artifact_content(self, parser):
        large_body = "x" * 10000
        text = f'''```email
{{"to": "a@b.com", "subject": "Large", "body": "{large_body}"}}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert len(artifacts[0].content["body"]) == 10000

    def test_remove_preserves_non_artifact_text(self, parser):
        text = '''Intro paragraph.

```task
{"title": "Remove me"}
```

Middle paragraph.

```python
print("Keep me — not a registered type")
```

Conclusion.'''
        cleaned = parser.remove_from_text(text)
        assert "Intro paragraph" in cleaned
        assert "Middle paragraph" in cleaned
        assert "Conclusion" in cleaned
        assert "Remove me" not in cleaned
        assert "```python" in cleaned  # Not a registered type, kept

    def test_remove_from_text_with_no_artifacts(self, parser):
        text = "Just regular text with no code blocks."
        cleaned = parser.remove_from_text(text)
        assert cleaned == text

    def test_positions_tracked(self, parser):
        text = '''Before
```task
{"title": "Positioned"}
```
After'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].start_pos > 0
        assert artifacts[0].end_pos > artifacts[0].start_pos


class TestCustomTypeRegistration:
    def test_register_and_parse(self):
        parser = ArtifactParser()
        parser.register_type(
            ["deployment", "deploy"],
            "deployment",
            required_fields=["target", "version"],
        )
        text = '''```deployment
{"target": "production", "version": "2.1.0", "rollback": true}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "deployment"

    def test_register_validates_required_fields(self):
        parser = ArtifactParser()
        parser.register_type(
            ["deployment"], "deployment", required_fields=["target", "version"]
        )
        text = '''```deployment
{"target": "staging"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 0  # Missing "version"

    def test_register_multiple_markers(self):
        parser = ArtifactParser()
        parser.register_type(["pr", "pull_request", "merge_request"], "pull_request")
        for marker in ["pr", "pull_request", "merge_request"]:
            text = f'''```{marker}
{{"title": "Test PR"}}
```'''
            artifacts = parser.parse(text)
            assert len(artifacts) == 1
            assert artifacts[0].artifact_type == "pull_request"

    def test_case_insensitive_markers(self, parser):
        text = '''```EMAIL
{"to": "a@b.com", "subject": "Upper", "body": "test"}
```'''
        # Our regex captures the marker, .lower() normalizes it
        artifacts = parser.parse(text)
        assert len(artifacts) == 1

    def test_override_existing_type(self):
        parser = ArtifactParser()
        parser.register_type(["email"], "custom_email", required_fields=["recipient"])
        text = '''```email
{"recipient": "test@x.com"}
```'''
        artifacts = parser.parse(text)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "custom_email"
