"""Unit tests for dispatcher orchestration and intake gate."""

from unittest.mock import AsyncMock
import pytest
from pathlib import Path

from research_pipeline.dispatcher import has_agent_outputs, run_pipeline


class TestHasAgentOutputs:
    """Test pure decision function for intake gate."""

    def test_both_empty_returns_false(self) -> None:
        kilo = {"text": "", "ok": False, "exit_code": -1}
        opencode = {"text": "", "ok": False, "exit_code": -1}
        assert has_agent_outputs(kilo, opencode) is False

    def test_whitespace_only_returns_false(self) -> None:
        kilo = {"text": "   \n\t ", "ok": False, "exit_code": 0}
        opencode = {"text": "", "ok": False, "exit_code": -1}
        assert has_agent_outputs(kilo, opencode) is False

    def test_kilo_only_returns_true(self) -> None:
        kilo = {"text": "Kilocode research finding", "ok": True, "exit_code": 0}
        opencode = {"text": "", "ok": False, "exit_code": -1}
        assert has_agent_outputs(kilo, opencode) is True

    def test_opencode_only_returns_true(self) -> None:
        kilo = {"text": "", "ok": False, "exit_code": -1}
        opencode = {"text": "Opencode research finding", "ok": True, "exit_code": 0}
        assert has_agent_outputs(kilo, opencode) is True

    def test_both_valid_returns_true(self) -> None:
        kilo = {"text": "Finding A", "ok": True, "exit_code": 0}
        opencode = {"text": "Finding B", "ok": True, "exit_code": 0}
        assert has_agent_outputs(kilo, opencode) is True



class TestIntakeGateIntegration:
    """Test that run_pipeline fails fast and produces no report when both agents fail."""

    @pytest.mark.anyio
    async def test_run_pipeline_aborts_when_both_agents_empty(self, tmp_path: Path, monkeypatch) -> None:
        task_file = tmp_path / "task.md"
        task_file.write_text("Smoke test task", encoding="utf-8")

        mock_kilo = AsyncMock(return_value={"text": "", "ok": False, "exit_code": -1, "stderr": "Failed"})
        mock_opencode = AsyncMock(return_value={"text": "", "ok": False, "exit_code": -1, "stderr": "Failed"})
        mock_summary = AsyncMock()

        monkeypatch.setattr("research_pipeline.dispatcher.run_kilocode", mock_kilo)
        monkeypatch.setattr("research_pipeline.dispatcher.run_opencode", mock_opencode)
        monkeypatch.setattr("research_pipeline.dispatcher.generate_cross_summary", mock_summary)
        monkeypatch.setattr("research_pipeline.dispatcher.REPORTS_DIR", tmp_path)

        with pytest.raises(RuntimeError, match="Both CLI agents failed or returned empty outputs"):
            await run_pipeline(task_file)

        # Verify Gemma was NOT called
        mock_summary.assert_not_called()

        # Verify NO report-*.md file was generated
        reports = list(tmp_path.glob("report-*.md"))
        assert len(reports) == 0


class TestEnrichOutputWithArtifacts:
    """Test discovering and attaching research/ artifacts to agent text."""

    def test_enrich_output_with_artifacts_attaches_discovered_files(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from research_pipeline.dispatcher import _enrich_output_with_artifacts

        research_dir = tmp_path / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "report.md").write_text(
            "# Detailed Benchmarks\nSorting is fast.", encoding="utf-8"
        )

        monkeypatch.setattr("research_pipeline.dispatcher.BASE_DIR", tmp_path)

        result = _enrich_output_with_artifacts("Agent summary chat text")

        assert "Agent summary chat text" in result
        assert "## Обнаруженные артефакты на диске" in result
        assert "### Артефакт: `research/report.md`" in result
        assert "Sorting is fast." in result


class TestRunMetricsAndScope:
    """Test per-run raw output scoping and metrics.json generation."""

    @pytest.mark.anyio
    async def test_run_pipeline_creates_run_dir_and_metrics_json(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import json

        task_file = tmp_path / "task.md"
        task_file.write_text("Task requirement", encoding="utf-8")

        mock_kilo = AsyncMock(
            return_value={
                "text": "Kilo report",
                "ok": True,
                "exit_code": 0,
                "stderr": None,
                "metrics": {"wall_time_s": 1.2, "events": [{"type": "step_finish"}]},
            }
        )
        mock_opencode = AsyncMock(
            return_value={
                "text": "Opencode report",
                "ok": True,
                "exit_code": 0,
                "stderr": None,
                "metrics": {"wall_time_s": 1.5, "events": []},
            }
        )
        mock_summary = AsyncMock(return_value="Cross summary text")

        monkeypatch.setattr("research_pipeline.dispatcher.run_kilocode", mock_kilo)
        monkeypatch.setattr("research_pipeline.dispatcher.run_opencode", mock_opencode)
        monkeypatch.setattr("research_pipeline.dispatcher.generate_cross_summary", mock_summary)
        monkeypatch.setattr("research_pipeline.dispatcher.REPORTS_DIR", tmp_path)

        report_path = await run_pipeline(task_file)
        assert report_path.exists()

        # Check run directory
        run_dirs = [d for d in tmp_path.glob("run-*") if d.is_dir()]
        assert len(run_dirs) == 1
        run_dir = run_dirs[0]

        assert (run_dir / "kilocode").is_dir()
        assert (run_dir / "opencode").is_dir()
        assert (run_dir / "kilocode-output.md").exists()
        assert (run_dir / "opencode-output.md").exists()
        assert (run_dir / "metrics.json").exists()

        # Check mock calls passed cwd
        assert mock_kilo.call_args.kwargs.get("cwd") == str(run_dir / "kilocode")
        assert mock_opencode.call_args.kwargs.get("cwd") == str(run_dir / "opencode")

        # Parse metrics.json
        meta = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        assert meta["kilocode"]["ok"] is True
        assert meta["kilocode"]["metrics"]["wall_time_s"] == 1.2
        assert meta["opencode"]["metrics"]["wall_time_s"] == 1.5



