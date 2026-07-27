# P1H-T1 — Task: Unbreak the install path and the 64 KiB NDJSON limit

> **Labels:** `wayfinder:task` `afk` `finding:C` `finding:A`  
> **Status:** resolved (2026-07-27)  
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question / work

Two verified defects sitting on the happy path. Both fixes are one-liners; both should land with a test.

### C — `.env.example` is physically malformed, so the documented install silently fails

`.env.example` is a **single 92-byte line** containing literal `\n` two-character sequences instead of newlines, plus a trailing CRLF.

Verified by parsing: after `cp .env.example .env` — exactly what [`README.md`](../README.md) instructs — a dotenv parser sees **zero** non-comment lines.

Consequence: no `GOOGLE_API_KEY` is set, so the pipeline takes the "key not set" branch and writes a **placeholder report** without ever failing loudly. It went unnoticed only because the working `.env` on this machine was hand-written, never copied.

Fix: rewrite `.env.example` with real LF newlines.

### A — an NDJSON line >64 KiB crashes the run *and* orphans the CLI child

`clients/agent_cli.py:88` — `line = await proc.stdout.readline()`.

`asyncio.StreamReader`'s default limit is 65536 bytes (verified on this machine: `asyncio.streams._DEFAULT_LIMIT == 65536`). A single 100 KB NDJSON line raises `ValueError: Separator is found, but chunk is longer than limit`.

`_run_cli` catches only `FileNotFoundError` (`agent_cli.py:71`) and `TimeoutError` (`agent_cli.py:108`), so the `ValueError` propagates through `run_pipeline` → `asyncio.run` as a bare traceback. Worse: that path never reaches `os.killpg` and never cancels `stderr_task`, so **the CLI child is orphaned** — defeating the process-group kill added in P1 hygiene.

Fix: pass an explicit `limit=` to `create_subprocess_exec`, and catch `ValueError` into the same soft-fail shape as the two existing handlers (so the child is still killed).

A real research run emits long tool-result and reasoning lines; 64 KiB is not a theoretical ceiling.

**Result:** `cp .env.example .env` yields a parseable file with a real key slot; an oversized NDJSON line soft-fails with the child process killed, covered by a unit test.

## Comments

- **2026-07-27 (Resolution):** Converted literal `\n` to LF newlines in `.env.example`. Passed `limit=10 * 1024 * 1024` (10 MiB) to `create_subprocess_exec` in `agent_cli.py`. Added `ValueError` handler in `_run_cli` and verified process group cleanup via `_cleanup_process`. Unit tests added in `test_agent_cli.py`. LGTM approved by Code Reviewer.

