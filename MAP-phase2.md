# Research Pipeline — Wayfinder Map Phase 2 (Verifier)

> **Label:** `wayfinder:map`  
> **Effort:** verifier-mvp  
> **Parent / prior map:** [MAP.md](MAP.md) (Phase 1 Dispatcher — destination reached)  
> **Prerequisite map:** [MAP-phase1-hardening.md](MAP-phase1-hardening.md) — Phase 1 currently produces the artifact Layer B judges **incorrectly** (fail-open reports, no provenance, chat abstracts instead of research). Its steps 1–2 and 4 land before Phase 2 work; its de-risk order does not disturb the one below.

## Destination

**MVP Verifier shipped and evaluated:** pipeline after Phase 1 report can run Layer A (code gates) + Layer B (JSON rubric vs `task.md` via **Hermes + Minimax M3 only**) + at most **one** targeted follow-up that **re-runs both CLIs** on a gap task only; second-pass material is **appended** under `## Follow-up`; `verdict.json` is written; human-agreeable verdicts shown on an eval set of tasks the human supplies as topics (agent formats `task.md`).

## Notes

- **Execution is in scope** for this map (destination is “shipped & eval’d”, not “spec only”). Prototype/task tickets may implement and run.
- **Plan default still holds for decisions:** grill/research before inventing product rules.
- **De-risk order (from independent audit):** do **not** implement Layer B / full Verifier ([P2-T5](tickets/P2-T5-verifier-mvp-prototype.md)) until [P2-T2](tickets/P2-T2-hermes-minimax-headless.md) proves Hermes+Minimax headless on this VPS (same class of surprises as T2 for Kilo/Opencode). Criteria ([P2-T1](tickets/P2-T1-quality-criteria-grilling.md)) should be locked before coding Layer B schema, not during.
- **Language / stack:** Python 3.12, `uv`, `src/research_pipeline/` — extend, don’t rewrite Phase 1. Prefer minimal deps (no framework sprawl unless a 30–60 min spike proves clear win).
- **CLI isolation & parallel dispatch (resolved 2026-07-27 in P1H-T6):** Kilocode and Opencode run in parallel (`asyncio.gather`) with isolated per-agent CWDs (`run-{timestamp}/kilocode/` and `run-{timestamp}/opencode/`) and sanitized environment (`_clean_env`).

- **Judge:** Hermes + Minimax M3 only (no Gemma-as-judge for Layer B). MiniMax is a **paid** path unlike free-tier Phase 1 CLIs — every design must assume cost.
- **Cost ceiling:** every Verifier cycle (Layer B call ± one dual-CLI follow-up) needs a **hard budget/config cap** (token $, wall time, or both) analogous to `CLI_TIMEOUT`. Exact numbers — grill/research; shipping without a ceiling is not OK.
- **Strictness:** prefer **false NEEDS_WORK** over false APPROVED (stricter judge).
- **Follow-up:** max 1; both CLIs; gap task only; append (not full merge). Manual/on-demand follow-up is fine for MVP; **unattended auto-follow-up / watch is gated on isolation** (see Not yet specified).
- **Degraded mode (standing rule to encode in Layer A):** if only one CLI succeeds → report is **partial**; Layer A must flag it; Layer B must not treat it as a full dual-agent report (no silent “looks fine”). Exact verdict mapping (NEEDS_WORK vs BLOCKED vs partial APPROVED) — [P2-T1](tickets/P2-T1-quality-criteria-grilling.md).
- **Research canon:** [`docs/research/verifier-phase2-findings.md`](docs/research/verifier-phase2-findings.md) (also force-added in git). External audit (2026-07) useful for ops risks; literature vs design split in findings still authoritative for sources.
- **Skills:** grilling, domain-modeling, prototype, research, oacp if multi-agent later.
- **Tracker layout (this repo):** map = `MAP-phase2.md`; tickets = `tickets/P2-T*.md` (same local-md pattern as Phase 1).

## Decisions so far

<!-- charting session 2026-07-24 — locked before tickets -->

- **Destination shape** — MVP Verifier shipped & eval’d (not spec-only, not full product/serve/Composer).
- **Layer B judge** — Hermes + Minimax M3 only.
- **Follow-up policy** — re-run both CLIs on gap task only; max 1; append `## Follow-up`.
- **Strictness** — prefer false NEEDS_WORK (don’t rubber-stamp thin reports).
- **Eval corpus** — human supplies topics; agent formats `tasks/eval/*.md`.

<!-- folded in from external audit 2026-07 — process constraints, not new product destination -->

- **De-risk before build** — Hermes headless (P2-T2) and criteria (P2-T1) before Verifier MVP code (P2-T5); do not skip.
- **Paid judge awareness** — cost ceiling required for a Verifier cycle (numbers TBD).
- **Partial dual-agent runs** — one-CLI success is degraded/partial, must surface in Layer A (mapping in P2-T1).
- **Sandbox before unattended loops** — no auto-watch / headless re-research farm until CLI isolation is decided (container / limited user / equivalent).

## Not yet specified

- Exact Layer B dimension list / JSON schema cutoffs (owned by [P2-T1](tickets/P2-T1-quality-criteria-grilling.md)); include degraded/partial mapping.
- Numeric **cost/time ceiling** for one Verifier cycle (Layer B ± follow-up); capture during P2-T1/T2 once Minimax pricing + Hermes latency known.
- Whether follow-up also re-runs Gemma cross-summary over combined material.
- Path naming: overwrite `report-*.md` vs always write `final_report.md`.
- Hermes install/auth/model-id/headless flags on this VPS (owned by [P2-T2](tickets/P2-T2-hermes-minimax-headless.md)).
- **CLI isolation design** for when follow-up becomes unattended (docker/firejail/restricted user) — gate for watch-mode; not a blocker for manual MVP runs.
- **Free-tier model alias drift** (kilo/opencode free proxies change backend without notice) — later: contract smoke on `tasks/smoke.md` / model ids (post-MVP or small hygiene ticket).
- Optional **short spike**: DeepEval/G-Eval (or similar) vs hand-rolled Layer B — only if it saves real work; default remains Hermes path unless spike wins. Not a destination change.
- Automation / watch / OACP for Verifier (after isolation + cost ceiling).
- Level 2 `kilo serve` / `opencode serve` (Phase 1 fog; still out of this destination unless reopened).
- Parallel CLI dispatch (latency only; out of critical path).

## Out of scope

- **Composer** (Hermes task author for free-form product tasks) — separate effort.
- **Full VeriMAP DAG planner / multi-round multi-agent debate** — scale mismatch (see findings).
- **Production serve + HTTP for CLIs** — Level 2; not required for MVP Verifier.
- **Gemma as Layer B judge** — rejected for this map.
- **Unbounded re-research loops** — max 1 follow-up fixed for MVP.
- **Replacing Hermes with an eval framework as the primary plan** — frameworks may inform Layer B shape (optional spike); they do not overturn the judge decision without a new grilling.
