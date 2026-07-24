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

## Comments
