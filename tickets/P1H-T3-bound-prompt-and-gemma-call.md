# P1H-T3 — Task: Bound the prompt and the Gemma call

> **Labels:** `wayfinder:task` `afk` `finding:B` `finding:F`  
> **Status:** resolved (2026-07-27)  
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question / work

Two unbounded inputs, neither of them handled. Both are the code-level face of premortem narrative **N7** (operational blind spots).

### B — the prompt is passed as argv, giving a hard ~128 KB ceiling that crashes

`agent_cli.py:30` (`cmd = ["kilo", "run", ..., prompt]`) and `agent_cli.py:43` put the **whole task text on the command line**.

Verified MAX_ARG_STRLEN behaviour on this machine: 131000 bytes OK, 131073 bytes → `OSError: Argument list too long`. Not caught anywhere → the run dies with a traceback.

Historical note worth keeping: T3's review accepted the item "`-f/--file` for large task.md — will handle in agent_cli.py". It was **never implemented**, and [`HANDOFF.md:97`](../HANDOFF.md) separately records that `-f` means "attach a file to the message", not "read the prompt from a file". So the problem was acknowledged, left unsolved, and the ticket closed anyway.

This ceiling will bite on large briefs and, sooner, on accumulated `## Follow-up` context once Phase 2 starts appending.

Fix: establish how each CLI actually reads a prompt from stdin or a file (the `-f` semantics above rule out the assumed route), and until then at minimum catch the `OSError` and soft-fail like the other handlers.

### F — the Gemma call has no timeout at all

`gemma.py:36,39` — `genai.Client()` then `generate_content` via a hand-rolled thread-pool shim. `CLI_TIMEOUT` (`config.py:16`) covers **only** the two CLIs. Because the call runs in a thread, `asyncio.timeout` cannot interrupt it: it can hang unbounded.

Phase 2 demands a "cost + wall-time ceiling" for every Verifier cycle, while the one paid call already in Phase 1 has neither.

Fix: give the Gemma call an explicit wall-time bound and a soft-fail path (a cross-summary that never returns must not hold the pipeline).

**Result:** an oversized task and a hanging Gemma call each fail predictably and soft, with a test for each.

## Comments
