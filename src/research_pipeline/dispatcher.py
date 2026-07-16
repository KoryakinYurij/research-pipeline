"""Dispatcher orchestration: read task → run CLI agents → cross-summary via Gemma → write report.

Implemented in T4 (Prototype).
Sequential execution by design — keeps the prototype simple and predictable.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_pipeline.clients.agent_cli import run_kilocode, run_opencode
from research_pipeline.clients.gemma import generate_cross_summary
from research_pipeline.config import CLI_TIMEOUT, REPORTS_DIR, TASKS_DIR, ensure_dirs


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
    print(f"   ({len(task_content)} chars)", flush=True)

    # 2. Run Kilocode
    print("\n🔧 Running Kilocode...", flush=True)
    kilo_result = await run_kilocode(task_content, timeout=CLI_TIMEOUT)
    _print_result("Kilocode", kilo_result)

    # 3. Run Opencode
    print("\n🔧 Running Opencode...", flush=True)
    opencode_result = await run_opencode(task_content, timeout=CLI_TIMEOUT)
    _print_result("Opencode", opencode_result)

    # 4. Save raw outputs
    kilo_path = REPORTS_DIR / "kilocode-output.md"
    opencode_path = REPORTS_DIR / "opencode-output.md"
    kilo_path.write_text(
        _format_raw_output("Kilocode", task_content, kilo_result), encoding="utf-8"
    )
    opencode_path.write_text(
        _format_raw_output("Opencode", task_content, opencode_result), encoding="utf-8"
    )
    print("\n💾 Raw outputs saved:", flush=True)
    print(f"   {kilo_path}", flush=True)
    print(f"   {opencode_path}", flush=True)

    # 5. Cross-summary via Gemma
    print("\n🧠 Generating cross-summary via Gemma 4 31B...", flush=True)
    kilo_text = kilo_result.get("text", "") or "_Пустой ответ_"
    opencode_text = opencode_result.get("text", "") or "_Пустой ответ_"
    try:
        cross_summary = await generate_cross_summary(kilo_text, opencode_text)
        print(f"   ({len(cross_summary)} chars)", flush=True)
    except Exception as e:
        cross_summary = (
            f"_Ошибка при генерации кросс-саммари: {e}_\n\n"
            "Проверьте GOOGLE_API_KEY в .env и доступность API."
        )
        print(f"   ❌ Failed: {e}", flush=True)

    # 6. Write final report
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = REPORTS_DIR / f"report-{timestamp}.md"

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
    print(f"\n✅ Report: {report_path}", flush=True)

    return report_path


def _print_result(label: str, result: dict) -> None:
    """Print a one-line status for a CLI result."""
    ok = result["ok"]
    text_len = len(result.get("text", ""))
    icon = "✅" if ok else "❌"
    stderr = f" stderr={result['stderr'][:60]}" if result.get("stderr") else ""
    print(f"   {icon} {label}: {text_len} chars, exit={result['exit_code']}{stderr}", flush=True)


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


def main() -> None:
    """Entry point for `uv run dispatcher` or `python -m research_pipeline`."""
    task_path = None
    if len(sys.argv) > 1:
        task_path = Path(sys.argv[1])
        if not task_path.exists():
            print(f"❌ File not found: {task_path}", file=sys.stderr, flush=True)
            sys.exit(1)

    asyncio.run(run_pipeline(task_path))


if __name__ == "__main__":
    main()
