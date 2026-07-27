# P1H-T4 — Grilling: What does a Phase 1 report actually contain?

> **Labels:** `wayfinder:grilling` `hitl` `finding:G` `finding:H`  
> **Status:** resolved (2026-07-27)  
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

## Comments

- **2026-07-27 (Resolution):** Passed `task.md` into `generate_cross_summary` prompt in `gemma.py` and updated system instruction for task coverage analysis. Added `_enrich_output_with_artifacts` in `dispatcher.py` to collect created files from agent workspaces (capped to 50 KiB per agent). Updated `CONTEXT.md` glossary definitions. Unit tests added in `test_dispatcher.py` and `test_gemma.py`. LGTM approved by Code Reviewer.

