"""Unit tests for Gemma cross-summary client."""

import asyncio
from unittest.mock import AsyncMock
import pytest

from research_pipeline.clients.gemma import generate_cross_summary


class TestGemmaTimeout:
    """Test timeout handling in generate_cross_summary."""

    @pytest.mark.anyio
    async def test_generate_cross_summary_timeout(self, monkeypatch) -> None:
        """Gemma call timing out raises TimeoutError with explicit message."""
        monkeypatch.setenv("GOOGLE_API_KEY", "dummy_key")
        monkeypatch.setenv("GEMINI_API_KEY", "dummy_key")
        monkeypatch.setattr(
            "research_pipeline.clients.gemma.GOOGLE_API_KEY", "dummy_key"
        )

        # Mock genai module
        from unittest.mock import MagicMock

        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        monkeypatch.setitem(
            pytest.importorskip("sys").modules, "google.genai", mock_genai
        )

        async def slow_to_thread(*args, **kwargs):
            await asyncio.sleep(10)
            return AsyncMock(text="late output")

        monkeypatch.setattr("asyncio.to_thread", slow_to_thread)

        with pytest.raises(TimeoutError, match="Gemma call timed out after 1s"):
            await generate_cross_summary(
                "task brief", "kilo data", "opencode data", timeout=1
            )


class TestBuildPrompt:
    """Test prompt assembly in gemma client."""

    def test_build_prompt_includes_task_content(self) -> None:
        from research_pipeline.clients.gemma import _build_prompt

        prompt = _build_prompt(
            "Compare sorting algorithms", "Kilo findings", "Opencode findings"
        )
        assert "## Исходное задание (task.md)" in prompt
        assert "Compare sorting algorithms" in prompt
        assert "## Отчёт Kilocode" in prompt
        assert "Kilo findings" in prompt
        assert "## Отчёт Opencode" in prompt
        assert "Opencode findings" in prompt
