# P2-T1 — Grilling: Quality criteria & Layer B rubric

> **Labels:** `wayfinder:grilling` `hitl`  
> **Status:** open  
> **Blocked by:** —  
> **Map:** [MAP-phase2.md](../MAP-phase2.md)

## Question

What exact acceptance criteria does Layer B use so the judge can emit a machine-gateable verdict?

Lock, with examples against a real or sample report:

1. **Required dimensions** (checklist items derived from `task.md` + report structure).  
   Candidates from research: `task_coverage`, `disagreement_handling`, `evidence_quality`, `actionable_gaps` / `missing[]`.
2. **JSON schema** for `verdict.json` (`APPROVED` | `NEEDS_WORK` | `BLOCKED`, scores, `missing[]`, `task_underspecified`, `followup_prompt`).
3. **Strict defaults** consistent with map decision (prefer false NEEDS_WORK): which single failed check forces NEEDS_WORK?
4. When is **BLOCKED** (task underspecified) vs NEEDS_WORK?
5. **Terminal state after an exhausted follow-up.** Policy is strict-bias + max 1 follow-up + both CLIs. If the report is *still* weak after that one follow-up, what verdict gets written? `NEEDS_WORK` forever (which makes `verdict.json` a label, not a gate), `APPROVED with caveat`, or `BLOCKED`? Undefined today — this ticket only covered intake (`BLOCKED` vs `NEEDS_WORK`), never exhaustion. Added from the 2026-07-27 audit (finding M).
6. What goes into **`task_followup.md`** (structure, language, length cap)?

**Already decided (do not re-open unless human overturns):** Hermes+Minimax only; max 1 follow-up; both CLIs; append Follow-up; strict bias.

**Blocked in practice on Phase 1 (audit 2026-07-27):**

- The **numeric cost ceiling** cannot be computed yet: Phase 1 discards the NDJSON `step_finish` events carrying tokens/cost (`agent_cli.py:154` drops everything that is not `type == "text"`). "Numbers TBD" will stay TBD by construction until [P1H-T5](P1H-T5-provenance-and-run-ids.md) records them. Finding L.
- `task_coverage` is **not computable on the current contract**: Gemma never sees `task.md` (`gemma.py:51-59`), and the report compares agent chat abstracts rather than the research the agents wrote to disk. Settle [P1H-T4](P1H-T4-report-contract-grilling.md) before locking the rubric — Layer B judges that artifact. Findings G/H.

**Result:** Written criteria + example `verdict.json` + example `task_followup.md` linked as assets. Domain terms in `CONTEXT.md` if new names stick.

## Comments
