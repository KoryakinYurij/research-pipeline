# Research Pipeline — Wayfinder Map Phase 2 (Verifier)

> **Label:** `wayfinder:map`  
> **Effort:** verifier-mvp  
> **Parent / prior map:** [MAP.md](MAP.md) (Phase 1 Dispatcher — destination reached)

## Destination

**MVP Verifier shipped and evaluated:** pipeline after Phase 1 report can run Layer A (code gates) + Layer B (JSON rubric vs `task.md` via **Hermes + Minimax M3 only**) + at most **one** targeted follow-up that **re-runs both CLIs** on a gap task only; second-pass material is **appended** under `## Follow-up`; `verdict.json` is written; human-agreeable verdicts shown on an eval set of tasks the human supplies as topics (agent formats `task.md`).

## Notes

- **Execution is in scope** for this map (destination is “shipped & eval’d”, not “spec only”). Prototype/task tickets may implement and run.
- **Plan default still holds for decisions:** grill/research before inventing product rules.
- **Language / stack:** Python 3.12, `uv`, `src/research_pipeline/` — extend, don’t rewrite Phase 1.
- **CLI order today:** Kilocode then Opencode **sequentially** (not parallel).
- **Judge:** Hermes + Minimax M3 only (no Gemma-as-judge for Layer B).
- **Strictness:** prefer **false NEEDS_WORK** over false APPROVED (stricter judge).
- **Follow-up:** max 1; both CLIs; gap task only; append (not full merge).
- **Research canon:** [`docs/research/verifier-phase2-findings.md`](docs/research/verifier-phase2-findings.md) (path under gitignored `docs/research/` — use `git add -f` if it must ship in git).
- **Skills:** grilling, domain-modeling, prototype, research, oacp if multi-agent later.
- **Tracker layout (this repo):** map = `MAP-phase2.md`; tickets = `tickets/P2-T*.md` (same local-md pattern as Phase 1).

## Decisions so far

<!-- charting session 2026-07-24 — locked before tickets -->

- **Destination shape** — MVP Verifier shipped & eval’d (not spec-only, not full product/serve/Composer).
- **Layer B judge** — Hermes + Minimax M3 only.
- **Follow-up policy** — re-run both CLIs on gap task only; max 1; append `## Follow-up`.
- **Strictness** — prefer false NEEDS_WORK (don’t rubber-stamp thin reports).
- **Eval corpus** — human supplies topics; agent formats `tasks/eval/*.md`.

## Not yet specified

- Exact Layer B dimension list / JSON schema cutoffs (partially owned by [P2-T1](tickets/P2-T1-quality-criteria-grilling.md)).
- Whether follow-up also re-runs Gemma cross-summary over combined material.
- Path naming: overwrite `report-*.md` vs always write `final_report.md`.
- Hermes install/auth facts on this VPS (owned by P2-T2 once researched).
- Automation / watch / OACP for Verifier.
- Level 2 `kilo serve` / `opencode serve` (Phase 1 fog; still out of this destination unless reopened).

## Out of scope

- **Composer** (Hermes task author for free-form product tasks) — separate effort.
- **Full VeriMAP DAG planner / multi-round multi-agent debate** — scale mismatch (see findings).
- **Production serve + HTTP for CLIs** — Level 2; not required for MVP Verifier.
- **Gemma as Layer B judge** — rejected for this map.
- **Unbounded re-research loops** — max 1 follow-up fixed for MVP.
