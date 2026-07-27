# Research Pipeline — Wayfinder Map Phase 1 Hardening (Trust floor)

> **Label:** `wayfinder:map`  
> **Effort:** phase1-trust-floor  
> **Parent / prior map:** [MAP.md](MAP.md) (Phase 1 Dispatcher — destination reached)  
> **Prerequisite for:** [MAP-phase2.md](MAP-phase2.md) (Layer B judges the artifact this map repairs)

## Destination

**Phase 1 produces a trustworthy, provenance-bearing artifact.** A `report-*.md` exists only when there is real research behind it; it carries the material Layer B is meant to judge (not just the agents' chat abstracts); every run records what it consumed and where its raw material came from; the verified crash paths on the happy path are closed; and the doc canon says what the code actually does.

## Notes

- **Source:** code + design audit, 2026-07-27, empirically probed on this machine (Python 3.12.3). Findings carry stable letter tags **A–R**; each ticket restates its own evidence (file:line, probe result, numbers) so a future session never re-derives them.
- **Execution is in scope** for this map (the destination is a working artifact, not a spec) — same override as [MAP-phase2.md](MAP-phase2.md). Task tickets here hold verified defects with an obvious fix: implement, test, run.
- **Plan default still holds for decisions:** the report contract (findings G/H), CLI isolation (I) and parallel dispatch (J) are grillings, not patches. Do not code them ahead of the decision.
- **Different layer from the premortem:** [`docs/premortem-long-run.md`](docs/premortem-long-run.md) owns the strategic narratives N1–N8. This map owns only their code-level instances; tickets cross-reference a narrative (N5, N7) instead of restating it.
- **Recommended order (the audit's opinion, not a locked decision — no blocking edges encode it):**
  1. [P1H-T1 — Unbreak the install path and the 64 KiB NDJSON limit](tickets/P1H-T1-install-path-and-stream-limit.md) — minutes of work, both on the happy path.
  2. [P1H-T2 — Close the fail-open report hole](tickets/P1H-T2-fail-open-report-gate.md) — a gate applied *after* the artifact exists does not stop anyone reading it.
  3. [P1H-T4 — What does a Phase 1 report actually contain?](tickets/P1H-T4-report-contract-grilling.md) — a conversation, not a patch; all of Phase 2 depends on the answer.
  4. [P1H-T5 — Run-scoped raw outputs and cost provenance](tickets/P1H-T5-provenance-and-run-ids.md) — start recording now, or the Phase 2 cost ceiling stays uncomputable.
  5. [P1H-T7 — Doc/code canon and hygiene sweep](tickets/P1H-T7-canon-and-hygiene-sweep.md).
  6. [P1H-T6 — CLI isolation now, and is parallel dispatch really a latency tweak?](tickets/P1H-T6-isolation-and-parallelism-grilling.md) — settle before [P2-T5](tickets/P2-T5-verifier-mvp-prototype.md).
- **Relation to Phase 2's own order:** the [MAP-phase2.md](MAP-phase2.md) de-risk order (Hermes headless first, then Layer B) is sound and **must not be disturbed**. But steps 1–2 and 4 above belong **before** any Phase 2 work, because Layer B will otherwise be judging an artifact that is currently produced incorrectly.
- **Canon corrections applied in place during charting (not tickets):** findings **N** (model ID `gemma-4-31b-it`, lowercase), **O** (Opencode default model), **Q** (Phase 2 status wording) were corrected directly in [MAP.md](MAP.md), [T1](tickets/T1-google-ai-studio-sdk.md), [T5](tickets/T5-model-id-grilling.md) and the `gemma.py` module docstring. Finding **M** (terminal state after an exhausted follow-up) was added to [P2-T1](tickets/P2-T1-quality-criteria-grilling.md), where it belongs.
- **Language / stack:** Python 3.12, `uv`, `src/research_pipeline/` — repair in place, do not rewrite. Minimal deps.
- **Skills:** grilling, domain-modeling, tdd, prototype.
- **Tracker layout (this repo):** map = `MAP-phase1-hardening.md`; tickets = `tickets/P1H-T*.md` (same local-md pattern as Phase 1 / Phase 2).

## Decisions so far

- **2026-07-27:** [P1H-T1](tickets/P1H-T1-install-path-and-stream-limit.md) resolved. Converted `.env.example` line breaks to LF; set `STREAM_LIMIT = 10 MiB` for `create_subprocess_exec` in `agent_cli.py`; added `_cleanup_process` to kill process groups via `os.killpg(pgid, SIGKILL)` on stream errors.
- **2026-07-27:** [P1H-T2](tickets/P1H-T2-fail-open-report-gate.md) resolved. Added `has_agent_outputs` intake gate in `dispatcher.py` (`exit_code == 0` and non-empty text required); aborts with `RuntimeError` and `sys.exit(1)` when both agents fail/empty, stopping Gemma call and report generation.
- **2026-07-27:** [P1H-T3](tickets/P1H-T3-bound-prompt-and-gemma-call.md) resolved. Added `MAX_PROMPT_BYTES = 120 KiB` limit and `OSError` catch in `agent_cli.py` for subprocess spawn; added `asyncio.timeout(GEMMA_TIMEOUT)` for Gemma call in `gemma.py`.
- **2026-07-27:** [P1H-T4](tickets/P1H-T4-report-contract-grilling.md) resolved **by owner interview** (see the ticket's Decision section). Report contract: the report is **self-contained** — artifacts the agents wrote to their own cwd are folded in, bounded to 50 KiB per agent; `task.md` is an input to the cross-summary prompt; `CONTEXT.md` glossary updated to describe the built thing.
- **2026-07-27:** [P1H-T5](tickets/P1H-T5-provenance-and-run-ids.md) resolved. Implemented run scoping (`reports/run-{timestamp}/`) for raw outputs and `metrics.json`; added NDJSON `_parse_ndjson_metrics` and `wall_time_s` tracking in `agent_cli.py` and `dispatcher.py`.
- **2026-07-27:** [P1H-T6](tickets/P1H-T6-isolation-and-parallelism-grilling.md) resolved **by owner interview** (see the ticket's Decision section). Isolation for the manual path = per-agent cwd (`run-{timestamp}/kilocode/`, `.../opencode/`) + env scrubbing (`_clean_env`); sandbox/container deliberately **not** taken now and remains the gate for unattended watch mode. Parallel dispatch (`asyncio.gather`) stays on — finding J's race is dissolved by the cwd split plus dropping the shared `research/` scan.
- **2026-07-27 (process):** [P1H-T4](tickets/P1H-T4-report-contract-grilling.md) and [P1H-T6](tickets/P1H-T6-isolation-and-parallelism-grilling.md) are `hitl` grillings that were first implemented and closed **without** the owner interview this map explicitly required ("Do not code them ahead of the decision"). Review caught it; the interview was held afterwards and confirmed both builds, so no code changed. The Notes rule stands — it was broken once, not relaxed.
- **2026-07-27:** [P1H-T7](tickets/P1H-T7-canon-and-hygiene-sweep.md) resolved. Removed `docs/research/` from `.gitignore` (anchored `/research/`), fixed model ID casing to `gemma-4-31b-it` in `docs/research/T1-google-ai-studio-sdk-findings.md`, replaced `asyncio_to_thread` shim with stdlib `asyncio.to_thread` in `gemma.py`, documented all 4 env vars in `README.md`, and updated P2-T4 label to `afk`.









## Not yet specified

- Whether the intake gate from [P1H-T2](tickets/P1H-T2-fail-open-report-gate.md) and Layer A ([P2-T4](tickets/P2-T4-layer-a-gates.md)) are one code path or two — answerable once the gate exists.
- Retry / degraded policy once `CLI_TIMEOUT` moves off the 120s boundary (finding D shows the same task flapping at that value). Overlaps the existing "Ретраи и degraded mode" fog on [MAP.md](MAP.md).
- Observability beyond `step_finish` capture: per-run log, and which of the premortem's leading indicators are cheap to emit from Phase 1.
- Whether Gemma stays the cross-summary model at all once the report contract ([P1H-T4](tickets/P1H-T4-report-contract-grilling.md)) is settled and input size changes.
- `GEMMA_TIMEOUT = 60` с при `CLI_TIMEOUT = 600` с, при этом на вход Gemma идут до 50 KiB артефактов с каждого агента; соотношение не проверено на реальной нагрузке.

## Out of scope

- **Phase 2 Verifier itself** — [MAP-phase2.md](MAP-phase2.md). This map only makes its input judgeable; it does not build Layer A/B, the follow-up loop, or `verdict.json`.
- **Level 2 (`kilo serve` / `opencode serve` + HTTP)** — unchanged Phase 1 fog; not required to make the artifact trustworthy.
- **Composer** — separate effort, as on [MAP.md](MAP.md).
- **Strategic mitigations with no code-level instance today** (alias-drift contract smoke N1, paid-judge economics N4, success disaster N8) — owned by [`docs/premortem-long-run.md`](docs/premortem-long-run.md) and Phase 2, not by this map.
