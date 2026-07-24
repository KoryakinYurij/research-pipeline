# Domain glossary — research-pipeline

Terms used by Phase 1 Dispatcher and Phase 2 Verifier. No implementation detail.

| Term | Meaning |
|------|---------|
| **Task** | The research brief in a markdown file (`task.md`) given to research agents. |
| **Report** | Combined artifact after agents run: raw agent outputs + optional cross-summary. |
| **Cross-summary** | Comparison of two agent outputs (common / diffs / watch-outs), currently via Gemma. |
| **Verifier** | Post-report step that judges quality against the Task and may request more research. |
| **Layer A** | Programmatic gates only (no LLM): emptiness, exit codes, required structure. |
| **Layer B** | Semantic rubric judged by an LLM against the Task (structured verdict). |
| **Verdict** | Machine result of verification: `APPROVED`, `NEEDS_WORK`, or `BLOCKED`. |
| **Gap task** | A short follow-up Task listing only missing/weak points (`task_followup.md`). |
| **Targeted follow-up** | At most one extra dual-CLI run driven by a gap task (not a full rewrite). |
| **False APPROVED** | Bad report labeled APPROVED — worse under our strictness policy. |
| **False NEEDS_WORK** | Good report labeled NEEDS_WORK — wastes a follow-up run. |
