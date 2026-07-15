"""Run Kilocode and Opencode CLI in headless mode (--format json, NDJSON stream).

Implemented in T4 (Prototype).
Key design decisions from T2:
- Primary approach: --format json → NDJSON in stdout, no TTY needed
- Production path: `opencode serve` / `kilo serve` (HTTP, async)
- Deprecated: script/pty wrapping (unreliable ANSI parsing)
"""


async def run_kilocode(prompt: str, timeout: int = 120) -> dict:
    """Run kilo run --auto --format json, parse NDJSON stream.

    Returns: {"text": str, "tokens": dict | None, "exit_code": int, "stderr": str | None}
    """
    raise NotImplementedError("T4")


async def run_opencode(prompt: str, timeout: int = 120) -> dict:
    """Run opencode run --dangerously-skip-permissions --format json, parse NDJSON stream.

    Returns: {"text": str, "tokens": dict | None, "exit_code": int, "stderr": str | None}
    """
    raise NotImplementedError("T4")
