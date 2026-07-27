# P1H-T4 — Grilling: What does a Phase 1 report actually contain?

> **Labels:** `wayfinder:grilling` `hitl` `finding:G` `finding:H`  
> **Status:** resolved (2026-07-27, owner interview) — see Decision below
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question

**The most important finding of the audit.** The advertised product is a "cross-summary of two independent research efforts". On a real task it degrades into a **comparison of two chat abstracts**. Decide what the report is — then everything downstream can be judged.

### G — the cross-summary compares agent replies, not research

In [`reports/report-20260722-102338.md`](../reports/report-20260722-102338.md) the Kilocode and Opencode sections read, in substance: "Benchmark done, results written to `research/sorting-comparison/report.md`, key conclusions: 1…4."

The actual research — a 10 KB report plus a `benchmark.py` — was written **by the agents to disk, outside the pipeline**. Gemma therefore received two four-bullet abstracts and faithfully compared *those*.

The defect is structural, not a prompt problem: `agent_cli` harvests only `type == "text"` events from the NDJSON stream (`agent_cli.py:154` returns `None` for anything else), and on-disk artifacts never re-enter the pipeline.

### H — Gemma never sees `task.md`

`gemma.py:51-59` (`_build_prompt`) sends **only the two agent outputs**. The system instruction asks the model to find "gaps and what to double-check" without telling it against *what*.

This breaks the Phase 2 seam directly: Layer B is specified to judge "vs `task.md`", yet the existing summarizer has never seen the task. The `task_coverage` dimension proposed in [P2-T1](P2-T1-quality-criteria-grilling.md) is **not computable** on the current contract.

### To settle

1. Does the report become **self-contained** — the pipeline collects the files the agents wrote and folds them in — or does the product get **renamed honestly** to what it does (comparison of agent summaries)?
2. If self-contained: how are agent-written artifacts discovered and bounded (which paths, what size cap, what happens to `benchmark.py`-style code)? Note this interacts with the isolation question in [P1H-T6](P1H-T6-isolation-and-parallelism-grilling.md) — you cannot collect from a sandbox you have not designed.
3. Does `task.md` enter the cross-summary prompt, and does that change Gemma's instruction?
4. Consequences for [`CONTEXT.md`](../CONTEXT.md): the glossary's **Report** and **Cross-summary** entries describe the intended thing, not the built thing.

**Blocks in spirit, not by edge:** all of Phase 2. Layer B judges this artifact, so [P2-T1](P2-T1-quality-criteria-grilling.md) rubric dimensions and [P2-T5](P2-T5-verifier-mvp-prototype.md) both rest on the answer. Resolve this before locking the rubric.

**Result:** a written report contract — what sections exist, what material they contain, whether `task.md` is an input to the summary — recorded here and reflected in `CONTEXT.md` if terms change.

## Decision (owner, 2026-07-27)

Answers to the four questions above, given by the owner in interview:

1. **The report becomes self-contained.** The pipeline collects what the agents wrote to disk and folds it into the report. The product is not renamed — it stays a cross-summary of two research efforts, and the pipeline is made to actually deliver that.
2. **Collection is bounded per agent:** only the agent's own working directory is scanned, individual files under 100 KiB, `MAX_ENRICH_BYTES = 50 KiB` total per agent, the last artifact truncated rather than dropped. Code files (`benchmark.py`-style) are attached like any other artifact. Accepted tradeoff: on large tasks the tail is cut — visible in the report as `(содержимое обрезано)`.
3. **Yes — `task.md` enters the cross-summary prompt**, and the system instruction now asks for task coverage first. Without this Phase 2's `task_coverage` dimension is not computable, so it was not treated as an open question.
4. **`CONTEXT.md` glossary updated** for **Report** and **Cross-summary** to describe the built thing.

## Comments

- **2026-07-27 (Implementation):** Passed `task.md` into `generate_cross_summary` prompt in `gemma.py` and updated system instruction for task coverage analysis. Added `_enrich_output_with_artifacts` in `dispatcher.py` to collect created files from agent workspaces (capped to 50 KiB per agent). Updated `CONTEXT.md` glossary definitions. Unit tests added in `test_dispatcher.py` and `test_gemma.py`.
- **2026-07-27 (Process defect, then correction):** This ticket was labelled `hitl` and the map said *"Do not code them ahead of the decision"*. It was implemented and closed **without the owner interview**. Review caught it; the interview was then held and its answers are recorded above. They happen to match what was built, so no code changed — but the decision is the owner's, recorded after the fact.

