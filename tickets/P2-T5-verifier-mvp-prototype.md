# P2-T5 — Prototype: Verifier MVP (Layer B + follow-up)

> **Labels:** `wayfinder:prototype` `hitl`  
> **Status:** open  
> **Blocked by:** P2-T1, P2-T2, P2-T4  
> **Map:** [MAP-phase2.md](../MAP-phase2.md)

## Question / prototype

Ship the MVP loop against real Phase 1 outputs:

```
report + task.md
  → Layer A (from P2-T4)
  → Layer B (Hermes + Minimax, schema from P2-T1)
  → APPROVED | NEEDS_WORK | BLOCKED
  → if NEEDS_WORK: write task_followup.md → run both CLIs once → append ## Follow-up
  → write verdict.json + final report artifact
```

Constraints from map:

- Judge: **Hermes + Minimax only**
- Max **1** follow-up; **both** CLIs; gap task only
- **Append** follow-up (no full merge engine)
- **Strict** defaults from P2-T1

**Result:** Runnable entrypoint (e.g. `uv run verifier path/to/task.md` or flag on dispatcher); human can smoke-test on one eval task.

**Collisions with existing Phase 1 code (audit 2026-07-27) — check before coding:**

- **Finding K — the follow-up will clobber pass one.** `dispatcher.py:42-43` writes raw outputs to fixed names (`kilocode-output.md`, `opencode-output.md`) while the report is timestamped. Re-running both CLIs for `## Follow-up` overwrites the first pass's raw material — exactly what Layer B was meant to compare. Needs [P1H-T5](P1H-T5-provenance-and-run-ids.md) first.
- **Finding J — the second run is not just slower, it races.** The map records parallel dispatch as "a latency tweak", but both CLIs get an identical prompt, hold write permission and share one cwd; they diverged into different directories by luck, and the CLIs have already written into `research/` and `docs/` unasked (finding I). A follow-up run doubles that exposure. Settle [P1H-T6](P1H-T6-isolation-and-parallelism-grilling.md) before this ticket.

## Comments
