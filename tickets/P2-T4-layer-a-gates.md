# P2-T4 — Prototype: Layer A programmatic gates

> **Labels:** `wayfinder:prototype` `hitl`  
> **Status:** open  
> **Blocked by:** —  
> **Map:** [MAP-phase2.md](../MAP-phase2.md)

## Question / prototype

Implement **cheap, code-only** checks (no LLM) on pipeline outputs so we fail fast before Hermes spend.

At minimum:

1. Non-empty Kilo / Opencode text (or explicit soft-fail flags from `agent_cli`).
2. At least one agent succeeded (`exit_code == 0` or equivalent).
3. Report file exists and contains expected section markers if we standardize them.
4. Clear structured result: pass/fail + list of failed gate ids (for `verdict.json` / logs).

Wire as a pure function + unit tests; optional hook from dispatcher or a thin `verify` entrypoint stub.

**Out of this ticket:** Layer B LLM judge, follow-up re-run.

**Result:** Code + tests; human reacts to API shape (pass/fail structure).

## Comments
