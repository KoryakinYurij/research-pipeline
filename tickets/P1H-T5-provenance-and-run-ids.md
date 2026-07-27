# P1H-T5 — Task: Run-scoped raw outputs and cost provenance

> **Labels:** `wayfinder:task` `afk` `finding:K` `finding:L`  
> **Status:** resolved (2026-07-27)  
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question / work

Phase 1 measures nothing and keeps nothing per run. Two consequences, both already scheduled to bite Phase 2. Start recording now.

### K — raw outputs are overwritten, which will break the planned Follow-up

`dispatcher.py:42-43` writes fixed filenames:

```python
kilo_path = REPORTS_DIR / "kilocode-output.md"
opencode_path = REPORTS_DIR / "opencode-output.md"
```

while the report itself is timestamped (`dispatcher.py:69`). Confirmed on disk: `reports/` holds four timestamped reports but exactly **one** `kilocode-output.md` and **one** `opencode-output.md`.

The second pass planned for `## Follow-up` in [P2-T5](P2-T5-verifier-mvp-prototype.md) re-runs both CLIs — and will **clobber the first pass's raw material**, which is precisely what Layer B was supposed to compare against. The interaction between the Phase 2 plan and the existing code was never checked.

Fix: scope raw output filenames by run id (the timestamp already computed for the report is enough).

### L — cost data is discarded at the door

The NDJSON stream carries `step_finish` events with tokens and cost (documented in the [T2 findings](T2-kilocode-opencode-cli.md)). But `_parse_ndjson_text` (`agent_cli.py:154`) returns `None` for anything whose `type` is not `"text"`:

```python
if obj.get("type") != "text":
```

So every token, model id and timing figure the CLIs report is thrown away.

Therefore the **numeric cost ceiling** required by [P2-T1](P2-T1-quality-criteria-grilling.md) / [P2-T2](P2-T2-hermes-minimax-headless.md) is *uncomputable*: the "numbers TBD" on [MAP-phase2.md](../MAP-phase2.md) will stay TBD **by construction**, not by neglect. There is no baseline to price a Verifier cycle against.

Fix: persist `step_finish` per run (tokens, model id, wall time) alongside the raw outputs. Storage shape can be minimal — this ticket is about not discarding the data, not about a metrics system.

**Result:** two consecutive runs keep both sets of raw outputs; each run leaves a machine-readable record of tokens/model/wall-time per CLI. Phase 2 can then compute a real ceiling.

## Comments

- **2026-07-27 (Resolution):** Implemented run scoping (`reports/run-{timestamp}/`) for raw outputs, `metrics.json`, and `report-{timestamp}.md`. Implemented `_parse_ndjson_metrics` and `wall_time_s` tracking using `time.monotonic()` in `agent_cli.py` and `dispatcher.py`. Unit tests added in `test_agent_cli.py` and `test_dispatcher.py`. LGTM approved by Code Reviewer.

