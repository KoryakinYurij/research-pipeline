"""Dispatcher orchestration: read task → run CLI agents → cross-summary via Gemma → write report.

Implemented in T4 (Prototype).
Sequential execution by design — keeps the prototype simple and predictable.
"""

import asyncio
import json
import sys

from datetime import datetime, timezone
from pathlib import Path

from research_pipeline.clients.agent_cli import run_kilocode, run_opencode
from research_pipeline.clients.gemma import generate_cross_summary
from research_pipeline.config import (
    BASE_DIR,
    CLI_TIMEOUT,
    REPORTS_DIR,
    TASKS_DIR,
    ensure_dirs,
)


def has_agent_outputs(kilo_result: dict, opencode_result: dict) -> bool:
    """Check if at least one CLI agent produced non-empty output.

    Pure intake gate decision function — returns True if any agent output is non-empty.
    """
    kilo_text = (kilo_result.get("text") or "").strip()
    opencode_text = (opencode_result.get("text") or "").strip()
    return bool(kilo_text or opencode_text)


async def run_pipeline(task_path: Path | None = None) -> Path:
    """Execute the full pipeline and return path to the generated report."""
    ensure_dirs()

    # 1. Read task
    if task_path is None:
        task_path = TASKS_DIR / "task.md"
    task_content = task_path.read_text(encoding="utf-8").strip()
    if not task_content:
        raise ValueError(f"Task file is empty: {task_path}")

    print(f"📋 Task: {task_path}", flush=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = REPORTS_DIR / f"run-{timestamp}"
    kilo_cwd = run_dir / "kilocode"
    opencode_cwd = run_dir / "opencode"
    kilo_cwd.mkdir(parents=True, exist_ok=True)
    opencode_cwd.mkdir(parents=True, exist_ok=True)

    # 2. Run Kilocode & Opencode in parallel
    print("\n🔧 Dispatching Kilocode & Opencode in parallel...", flush=True)
    kilo_result, opencode_result = await asyncio.gather(
        run_kilocode(task_content, timeout=CLI_TIMEOUT, cwd=str(kilo_cwd)),
        run_opencode(task_content, timeout=CLI_TIMEOUT, cwd=str(opencode_cwd)),
    )
    _print_result("Kilocode", kilo_result)
    _print_result("Opencode", opencode_result)

    # 3. Intake Gate Check
    if not has_agent_outputs(kilo_result, opencode_result):
        raise RuntimeError(
            "Both CLI agents failed or returned empty outputs. "
            "Pipeline aborted: no report generated."
        )

    # 4. Save run-scoped raw outputs and metrics
    kilo_path = run_dir / "kilocode-output.md"
    opencode_path = run_dir / "opencode-output.md"
    metrics_path = run_dir / "metrics.json"

    kilo_path.write_text(
        _format_raw_output("Kilocode", task_content, kilo_result), encoding="utf-8"
    )
    opencode_path.write_text(
        _format_raw_output("Opencode", task_content, opencode_result), encoding="utf-8"
    )

    metrics_data = {
        "run_id": f"run-{timestamp}",
        "timestamp": timestamp,
        "task_file": task_path.name,
        "kilocode": {
            "ok": kilo_result.get("ok"),
            "exit_code": kilo_result.get("exit_code"),
            "stderr": kilo_result.get("stderr"),
            "metrics": kilo_result.get("metrics", {}),
        },
        "opencode": {
            "ok": opencode_result.get("ok"),
            "exit_code": opencode_result.get("exit_code"),
            "stderr": opencode_result.get("stderr"),
            "metrics": opencode_result.get("metrics", {}),
        },
    }
    metrics_path.write_text(
        json.dumps(metrics_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n💾 Run-scoped raw outputs and metrics saved:", flush=True)
    print(f"   {run_dir}", flush=True)

    # 5. Cross-summary via Gemma
    print("\n🧠 Generating cross-summary via Gemma 4 31B...", flush=True)
    kilo_raw = (kilo_result.get("text") or "").strip()
    kilo_text = (
        _enrich_output_with_artifacts(kilo_raw, kilo_cwd)
        if kilo_raw
        else f"_FAILED (exit_code: {kilo_result.get('exit_code')}, stderr: {kilo_result.get('stderr') or 'empty output'})_"
    )

    opencode_raw = (opencode_result.get("text") or "").strip()
    opencode_text = (
        _enrich_output_with_artifacts(opencode_raw, opencode_cwd)
        if opencode_raw
        else f"_FAILED (exit_code: {opencode_result.get('exit_code')}, stderr: {opencode_result.get('stderr') or 'empty output'})_"
    )

    try:
        cross_summary = await generate_cross_summary(
            task_content, kilo_text, opencode_text
        )
        print(f"   ({len(cross_summary)} chars)", flush=True)
    except Exception as e:
        cross_summary = (
            f"_Ошибка при генерации кросс-саммари: {e}_\n\n"
            "Проверьте GOOGLE_API_KEY в .env и доступность API."
        )
        print(f"   ❌ Failed: {e}", flush=True)


    # 7. Write final report
    report_path = run_dir / f"report-{timestamp}.md"
    root_report_path = REPORTS_DIR / f"report-{timestamp}.md"

    report = (
        f"# Cross-Summary\n\n"
        f"{cross_summary}\n\n"
        f"---\n\n"
        f"# Kilocode Output\n\n"
        f"_exit_code: {kilo_result.get('exit_code')}, "
        f"errors: {'yes' if kilo_result.get('stderr') else 'none'}_\n\n"
        f"{kilo_text}\n\n"
        f"---\n\n"
        f"# Opencode Output\n\n"
        f"_exit_code: {opencode_result.get('exit_code')}, "
        f"errors: {'yes' if opencode_result.get('stderr') else 'none'}_\n\n"

        f"{opencode_text}\n\n"
        f"---\n\n"
        f"_Generated: {timestamp} UTC | Task: {task_path.name}_\n"
    )
    report_path.write_text(report, encoding="utf-8")
    root_report_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Report: {report_path}", flush=True)

    return report_path



def _print_result(label: str, result: dict) -> None:
    """Print a one-line status for a CLI result."""
    ok = result["ok"]
    text_len = len(result.get("text", ""))
    icon = "✅" if ok else "❌"
    stderr = f" stderr={result['stderr'][:60]}" if result.get("stderr") else ""
    print(
        f"   {icon} {label}: {text_len} chars, exit={result['exit_code']}{stderr}",
        flush=True,
    )


def _format_raw_output(label: str, prompt: str, result: dict) -> str:
    """Format a raw CLI output for saving to disk."""
    return (
        f"# {label} — Raw Output\n\n"
        f"**Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n\n"
        f"**Exit code:** {result['exit_code']}\n\n"
        f"**Stderr:** {result.get('stderr') or 'none'}\n\n"
        f"---\n\n"
        f"{result.get('text', '') or '_No output_'}\n"
    )


def _enrich_output_with_artifacts(text: str, agent_cwd: Path | None = None) -> str:
    """Enrich agent chat text output with discovered files from agent workspace or research/."""
    text_clean = text.strip()
    dirs_to_check = []
    if agent_cwd and agent_cwd.exists():
        dirs_to_check.append(agent_cwd)
    research_dir = BASE_DIR / "research"
    if research_dir.exists():
        dirs_to_check.append(research_dir)

    if not dirs_to_check:
        return text_clean

    artifact_sections = []
    seen_paths = set()

    for search_dir in dirs_to_check:
        for p in sorted(search_dir.rglob("*")):
            if (
                p.is_file()
                and p.suffix in (".md", ".py", ".txt", ".json")
                and p.stat().st_size < 100 * 1024
                and p not in seen_paths
            ):
                seen_paths.add(p)
                try:
                    rel = p.relative_to(BASE_DIR)
                except ValueError:
                    rel = p.name
                content = p.read_text(encoding="utf-8", errors="replace").strip()
                if content and content not in text_clean:
                    artifact_sections.append(
                        f"\n\n### Артефакт: `{rel}`\n\n```\n{content}\n```"
                    )

    if artifact_sections:
        return text_clean + "\n\n## Обнаруженные артефакты на диске\n" + "".join(artifact_sections)
    return text_clean



def main() -> None:

    """Entry point for `uv run dispatcher` or `python -m research_pipeline`."""
    task_path = None
    if len(sys.argv) > 1:
        task_path = Path(sys.argv[1])
        if not task_path.exists():
            print(f"❌ File not found: {task_path}", file=sys.stderr, flush=True)
            sys.exit(1)

    try:
        asyncio.run(run_pipeline(task_path))
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}", file=sys.stderr, flush=True)
        sys.exit(1)



if __name__ == "__main__":
    main()
