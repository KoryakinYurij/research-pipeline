"""Run Kilocode and Opencode CLI via direct subprocess with --format json (NDJSON).

Implemented in T4 (Prototype).
Key design decisions:
- Direct asyncio.create_subprocess_exec — no shell, no escaping issues with multi-line prompts
- stdin=DEVNULL — critical: both CLIs hang waiting for stdin otherwise
- Free-tier models: kilo/kilo-auto/free and opencode/deepseek-v4-flash-free
- --format json produces clean NDJSON: {"type":"text", "part":{"text":"..."}}
- stderr read concurrently to avoid pipe-buffer deadlock
- asyncio.timeout() for overall timeout control
- start_new_session + os.killpg on timeout — prevents orphaned child processes
- FileNotFoundError caught — graceful failure when CLI is not installed
"""

import asyncio
import json
import os
import signal
import time


STREAM_LIMIT = (
    10 * 1024 * 1024
)  # 10 MiB limit for NDJSON lines (default asyncio limit is 64 KiB)
MAX_PROMPT_BYTES = (
    120 * 1024
)  # 120 KiB — headroom under the measured single-argv ceiling (131072 B on Linux)


def _clean_env() -> dict[str, str]:
    """Return sanitized environment dict removing sensitive API keys for CLI subprocesses."""
    env = dict(os.environ)
    for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(key, None)
    return env


async def run_kilocode(
    prompt: str,
    timeout: int = 120,
    model: str = "kilo/kilo-auto/free",
    cwd: str | None = None,
) -> dict:
    """Run kilo with --format json, capturing NDJSON text chunks.

    Returns: {"text": str, "exit_code": int, "stderr": str, "ok": bool}
    """
    cmd = ["kilo", "run", "--auto", "--model", model, "--format", "json", prompt]
    return await _run_cli(cmd, timeout, cwd=cwd)


async def run_opencode(
    prompt: str,
    timeout: int = 120,
    model: str = "opencode/deepseek-v4-flash-free",
    cwd: str | None = None,
) -> dict:
    """Run opencode with --format json, capturing NDJSON text chunks.

    Returns: {"text": str, "exit_code": int, "stderr": str, "ok": bool}
    """
    cmd = [
        "opencode",
        "run",
        "--dangerously-skip-permissions",
        "-m",
        model,
        "--format",
        "json",
        prompt,
    ]
    return await _run_cli(cmd, timeout, cwd=cwd)


async def _run_cli(
    cmd: list[str],
    timeout: int,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Execute CLI, parse NDJSON stdout, collect text chunks and cost/token metrics.

    stdin=DEVNULL is critical — without it both CLIs hang waiting for input.
    stderr is read concurrently to avoid pipe-buffer deadlock.
    start_new_session + os.killpg on timeout or stream error ensures no orphaned child processes.
    """
    start_time = time.monotonic()
    metrics_events: list[dict] = []
    effective_env = env if env is not None else _clean_env()

    prompt_arg = cmd[-1] if cmd else ""
    prompt_bytes = len(prompt_arg.encode("utf-8"))
    if prompt_bytes > MAX_PROMPT_BYTES:
        return {
            "text": "",
            "exit_code": -1,
            "stderr": (
                f"Prompt size ({prompt_bytes} bytes) "
                f"exceeds MAX_PROMPT_BYTES ({MAX_PROMPT_BYTES} bytes). Spawn aborted."
            ),
            "ok": False,
            "metrics": {"wall_time_s": 0.0, "events": []},
        }

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=STREAM_LIMIT,
            start_new_session=True,
            cwd=cwd,
            env=effective_env,
        )

    except FileNotFoundError:
        binary = cmd[0]
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"CLI not found: {binary}. Is it installed?",
            "ok": False,
            "metrics": {"wall_time_s": 0.0, "events": []},
        }
    except OSError as e:
        binary = cmd[0]
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"Failed to spawn CLI {binary}: {e}",
            "ok": False,
            "metrics": {"wall_time_s": 0.0, "events": []},
        }

    # Read stderr concurrently to avoid pipe-buffer deadlock
    stderr_task = asyncio.create_task(_read_stream(proc.stderr))

    text_parts: list[str] = []

    try:
        async with asyncio.timeout(timeout):
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    obj = json.loads(line_str)
                except json.JSONDecodeError:
                    continue

                # Real NDJSON text chunk: {"type":"text", "part":{"text":"..."}}
                chunk = _parse_ndjson_text(obj)
                if chunk:
                    text_parts.append(chunk)

                # Collect metrics/step_finish events if present
                metrics_info = _parse_ndjson_metrics(obj)
                if metrics_info:
                    metrics_events.append(metrics_info)

            await proc.wait()

    except TimeoutError:
        await _cleanup_process(proc, stderr_task)
        wall_time_s = round(time.monotonic() - start_time, 2)
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"Timeout after {timeout}s",
            "ok": False,
            "metrics": {"wall_time_s": wall_time_s, "events": metrics_events},
        }
    except ValueError as e:
        await _cleanup_process(proc, stderr_task)
        wall_time_s = round(time.monotonic() - start_time, 2)
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"Stream read error: {e}",
            "ok": False,
            "metrics": {"wall_time_s": wall_time_s, "events": metrics_events},
        }

    stderr_bytes = await stderr_task
    stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()
    text = "".join(text_parts)
    exit_code = proc.returncode if proc.returncode is not None else -1
    wall_time_s = round(time.monotonic() - start_time, 2)

    return {
        "text": text,
        "exit_code": exit_code,
        "stderr": stderr_str or None,
        "ok": (exit_code == 0 and bool(text.strip())),
        "metrics": {
            "wall_time_s": wall_time_s,
            "events": metrics_events,
        },
    }


async def _cleanup_process(
    proc: asyncio.subprocess.Process, stderr_task: asyncio.Task
) -> None:
    """Kill process group and cancel stderr reader task safely."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, OSError):
        proc.kill()
    await proc.wait()
    stderr_task.cancel()


async def _read_stream(stream: asyncio.StreamReader) -> bytes:
    """Read an entire stream (used for concurrent stderr capture)."""
    chunks: list[bytes] = []
    while True:
        chunk = await stream.read(8192)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _parse_ndjson_text(obj: dict) -> str | None:
    """Extract text from a parsed NDJSON object.

    Real NDJSON structure: {"type":"text", "part":{"text":"..."}}
    Returns the text string if found, None otherwise.
    Pure function — no I/O, testable without subprocess.
    """
    if not isinstance(obj, dict):
        return None
    if obj.get("type") != "text":
        return None
    part = obj.get("part")
    if not isinstance(part, dict):
        return None
    chunk = part.get("text")
    if isinstance(chunk, str):
        return chunk
    return None


def _parse_ndjson_metrics(obj: dict) -> dict | None:
    """Extract metrics (tokens, model, cost, step_finish) from NDJSON object if present."""
    if not isinstance(obj, dict):
        return None

    obj_type = obj.get("type")
    part = obj.get("part") if isinstance(obj.get("part"), dict) else {}

    is_finish = obj_type in ("step_finish", "finish") or part.get("type") in (
        "step-finish",
        "finish",
    )
    has_stats = any(
        k in obj or k in part for k in ("tokens", "usage", "cost", "model", "stats")
    )

    if not (is_finish or has_stats):
        return None

    metrics: dict = {}
    if obj_type:
        metrics["type"] = obj_type

    for source in (part, obj):
        if "model" in source and "model" not in metrics:
            metrics["model"] = source["model"]
        if "tokens" in source and "tokens" not in metrics:
            metrics["tokens"] = source["tokens"]
        if "usage" in source and "usage" not in metrics:
            metrics["usage"] = source["usage"]
        if "cost" in source and "cost" not in metrics:
            metrics["cost"] = source["cost"]

    if is_finish and part:
        metrics["part"] = part

    return metrics if metrics else None
