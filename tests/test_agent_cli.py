"""Unit tests for agent_cli NDJSON parsing — pure logic, no subprocess needed."""

from research_pipeline.clients.agent_cli import _parse_ndjson_text


class TestParseNdjsonText:
    """The real NDJSON structure is {\"type\": \"text\", \"part\": {\"text\": \"...\"}}."""

    def test_real_structure_extracts_text(self) -> None:
        obj = {"type": "text", "part": {"text": "pong"}}
        assert _parse_ndjson_text(obj) == "pong"

    def test_real_structure_multi_char(self) -> None:
        obj = {"type": "text", "part": {"text": "hello world"}}
        assert _parse_ndjson_text(obj) == "hello world"

    def test_real_structure_empty_string(self) -> None:
        obj = {"type": "text", "part": {"text": ""}}
        assert _parse_ndjson_text(obj) == ""

    def test_wrong_type_not_text(self) -> None:
        """Non-text types (step_start, step_finish) should be ignored."""
        obj = {"type": "step_start", "part": {"id": "abc"}}
        assert _parse_ndjson_text(obj) is None

    def test_missing_part(self) -> None:
        obj = {"type": "text"}
        assert _parse_ndjson_text(obj) is None

    def test_part_not_dict(self) -> None:
        obj = {"type": "text", "part": "not-a-dict"}
        assert _parse_ndjson_text(obj) is None

    def test_missing_text_in_part(self) -> None:
        obj = {"type": "text", "part": {"other": "value"}}
        assert _parse_ndjson_text(obj) is None

    def test_text_not_string(self) -> None:
        obj = {"type": "text", "part": {"text": 42}}
        assert _parse_ndjson_text(obj) is None

    def test_not_dict_input(self) -> None:
        assert _parse_ndjson_text("not a dict") is None  # type: ignore[arg-type]
        assert _parse_ndjson_text(None) is None  # type: ignore[arg-type]

    def test_empty_dict(self) -> None:
        assert _parse_ndjson_text({}) is None

    def test_flat_text_property(self) -> None:
        """Common mistaken format: {\"type\":\"text\", \"text\":\"...\"} — should NOT extract."""
        obj = {"type": "text", "text": "wrong-level"}
        assert _parse_ndjson_text(obj) is None
