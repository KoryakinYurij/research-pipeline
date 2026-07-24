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
5. What goes into **`task_followup.md`** (structure, language, length cap)?

**Already decided (do not re-open unless human overturns):** Hermes+Minimax only; max 1 follow-up; both CLIs; append Follow-up; strict bias.

**Result:** Written criteria + example `verdict.json` + example `task_followup.md` linked as assets. Domain terms in `CONTEXT.md` if new names stick.

## Comments
