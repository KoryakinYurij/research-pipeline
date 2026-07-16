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


async def run_kilocode(
    prompt: str,
    timeout: int = 120,
    model: str = "kilo/kilo-auto/free",
) -> dict:
    """Run kilo with --format json, capturing NDJSON text chunks.

    Returns: {"text": str, "exit_code": int, "stderr": str, "ok": bool}
    """
    cmd = ["kilo", "run", "--auto", "--model", model, "--format", "json", prompt]
    return await _run_cli(cmd, timeout)


async def run_opencode(
    prompt: str,
    timeout: int = 120,
    model: str = "opencode/deepseek-v4-flash-free",
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
    return await _run_cli(cmd, timeout)


async def _run_cli(cmd: list[str], timeout: int) -> dict:
    """Execute CLI, parse NDJSON stdout, collect text chunks.

    stdin=DEVNULL is critical — without it both CLIs hang waiting for input.
    stderr is read concurrently to avoid pipe-buffer deadlock.
    start_new_session + os.killpg on timeout ensures no orphaned child processes.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
    except FileNotFoundError:
        binary = cmd[0]
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"CLI not found: {binary}. Is it installed?",
            "ok": False,
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

                # Real NDJSON: {"type":"text", "part":{"text":"..."}}
                chunk = _parse_ndjson_text(obj)
                if chunk:
                    text_parts.append(chunk)

            await proc.wait()

    except TimeoutError:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, OSError):
            proc.kill()
        await proc.wait()
        stderr_task.cancel()
        return {
            "text": "",
            "exit_code": -1,
            "stderr": f"Timeout after {timeout}s",
            "ok": False,
        }

    stderr_bytes = await stderr_task
    stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

    return {
        "text": "".join(text_parts),
        "exit_code": proc.returncode or 0,
        "stderr": stderr_str or None,
        "ok": (proc.returncode == 0),
    }


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
