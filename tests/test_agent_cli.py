import pytest

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
        """Flat format {"type":"text", "text":"..."} returns None (real NDJSON has part.text).

        Unrecognized shapes yield empty text, causing ok=False in _run_cli and triggering the P1H-T2 intake gate.
        """
        obj = {"type": "text", "text": "wrong-level"}
        assert _parse_ndjson_text(obj) is None


class TestStreamLimitAndErrorHandling:
    """Test STREAM_LIMIT constant and error handling in _run_cli."""

    def test_stream_limit_is_10mb(self) -> None:
        from research_pipeline.clients.agent_cli import STREAM_LIMIT

        assert STREAM_LIMIT == 10 * 1024 * 1024

    @pytest.mark.anyio
    async def test_run_cli_handles_value_error(self, monkeypatch) -> None:
        """ValueError during stdout readline (chunk longer than limit) soft-fails gracefully."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from research_pipeline.clients.agent_cli import _run_cli

        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.wait = AsyncMock()
        mock_proc.stdout.readline = AsyncMock(
            side_effect=ValueError("Separator is found, but chunk is longer than limit")
        )
        mock_proc.stderr = AsyncMock()
        mock_proc.stderr.read = AsyncMock(return_value=b"")

        mock_create = AsyncMock(return_value=mock_proc)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create)
        monkeypatch.setattr("os.getpgid", lambda pid: pid)
        monkeypatch.setattr("os.killpg", lambda pgid, sig: None)

        res = await _run_cli(["fake_cli"], timeout=5)

        assert res["ok"] is False
        assert res["exit_code"] == -1
        assert "Stream read error" in res["stderr"]

    @pytest.mark.anyio
    async def test_run_cli_handles_os_error(self, monkeypatch) -> None:
        """OSError during process spawn (e.g. Argument list too long) soft-fails gracefully."""
        import asyncio
        from unittest.mock import AsyncMock
        from research_pipeline.clients.agent_cli import _run_cli

        mock_create = AsyncMock(side_effect=OSError(7, "Argument list too long"))

        monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create)

        res = await _run_cli(["fake_cli"], timeout=5)

        assert res["ok"] is False
        assert res["exit_code"] == -1
        assert "Failed to spawn CLI fake_cli" in res["stderr"]
        assert "Argument list too long" in res["stderr"]

    @pytest.mark.anyio
    async def test_run_cli_rejects_oversized_prompt(self) -> None:
        """Prompts exceeding MAX_PROMPT_BYTES (120 KiB) are rejected before process spawn."""
        from research_pipeline.clients.agent_cli import MAX_PROMPT_BYTES, _run_cli

        oversized_prompt = "x" * (MAX_PROMPT_BYTES + 1024)
        res = await _run_cli(["fake_cli", oversized_prompt], timeout=5)

        assert res["ok"] is False
        assert res["exit_code"] == -1
        assert "exceeds MAX_PROMPT_BYTES" in res["stderr"]
        assert "Spawn aborted" in res["stderr"]



class TestParseNdjsonMetrics:
    """Test extracting metrics and finish events from NDJSON stream."""

    def test_parse_step_finish_event(self) -> None:
        from research_pipeline.clients.agent_cli import _parse_ndjson_metrics

        obj = {
            "type": "step_finish",
            "part": {
                "id": "step1",
                "type": "step-finish",
                "model": "kilo/free",
                "tokens": {"input": 120, "output": 45},
            },
        }
        res = _parse_ndjson_metrics(obj)
        assert res is not None
        assert res["type"] == "step_finish"
        assert res["model"] == "kilo/free"
        assert res["tokens"] == {"input": 120, "output": 45}

    def test_parse_text_event_returns_none(self) -> None:
        from research_pipeline.clients.agent_cli import _parse_ndjson_metrics

        obj = {"type": "text", "part": {"text": "hello"}}
        assert _parse_ndjson_metrics(obj) is None


class TestCleanEnv:
    """Test environment scrubbing for CLI subprocesses."""

    def test_clean_env_removes_sensitive_keys(self, monkeypatch) -> None:
        from research_pipeline.clients.agent_cli import _clean_env

        monkeypatch.setenv("GOOGLE_API_KEY", "secret_google")
        monkeypatch.setenv("GEMINI_API_KEY", "secret_gemini")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "secret_anthropic")
        monkeypatch.setenv("PATH", "/usr/bin")

        cleaned = _clean_env()

        assert "GOOGLE_API_KEY" not in cleaned
        assert "GEMINI_API_KEY" not in cleaned
        assert "ANTHROPIC_API_KEY" not in cleaned
        assert cleaned.get("PATH") == "/usr/bin"


class TestCwdDirFlag:
    """Test --dir flag inclusion when cwd is passed vs omitted."""

    @pytest.mark.anyio
    async def test_run_kilocode_includes_dir_when_cwd_set(self, monkeypatch) -> None:
        from research_pipeline.clients import agent_cli

        captured_cmd = []

        async def mock_run_cli(cmd, timeout, cwd=None, env=None):
            nonlocal captured_cmd
            captured_cmd = cmd
            return {"text": "ok", "exit_code": 0, "stderr": None, "ok": True}

        monkeypatch.setattr(agent_cli, "_run_cli", mock_run_cli)

        await agent_cli.run_kilocode("test prompt", cwd="/tmp/kilo_dir")
        assert captured_cmd[0:3] == ["kilo", "run", "--dir"]
        assert "/tmp/kilo_dir" in captured_cmd

    @pytest.mark.anyio
    async def test_run_kilocode_omits_dir_when_cwd_none(self, monkeypatch) -> None:
        from research_pipeline.clients import agent_cli

        captured_cmd = []

        async def mock_run_cli(cmd, timeout, cwd=None, env=None):
            nonlocal captured_cmd
            captured_cmd = cmd
            return {"text": "ok", "exit_code": 0, "stderr": None, "ok": True}

        monkeypatch.setattr(agent_cli, "_run_cli", mock_run_cli)

        await agent_cli.run_kilocode("test prompt", cwd=None)
        assert "--dir" not in captured_cmd

    @pytest.mark.anyio
    async def test_run_opencode_includes_dir_when_cwd_set(self, monkeypatch) -> None:
        from research_pipeline.clients import agent_cli

        captured_cmd = []

        async def mock_run_cli(cmd, timeout, cwd=None, env=None):
            nonlocal captured_cmd
            captured_cmd = cmd
            return {"text": "ok", "exit_code": 0, "stderr": None, "ok": True}

        monkeypatch.setattr(agent_cli, "_run_cli", mock_run_cli)

        await agent_cli.run_opencode("test prompt", cwd="/tmp/open_dir")
        assert captured_cmd[0:3] == ["opencode", "run", "--dir"]
        assert "/tmp/open_dir" in captured_cmd

    @pytest.mark.anyio
    async def test_run_opencode_omits_dir_when_cwd_none(self, monkeypatch) -> None:
        from research_pipeline.clients import agent_cli

        captured_cmd = []

        async def mock_run_cli(cmd, timeout, cwd=None, env=None):
            nonlocal captured_cmd
            captured_cmd = cmd
            return {"text": "ok", "exit_code": 0, "stderr": None, "ok": True}

        monkeypatch.setattr(agent_cli, "_run_cli", mock_run_cli)

        await agent_cli.run_opencode("test prompt", cwd=None)
        assert "--dir" not in captured_cmd
