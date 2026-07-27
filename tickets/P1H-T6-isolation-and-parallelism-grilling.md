# P1H-T6 — Grilling: CLI isolation now, and is parallel dispatch really a latency tweak?

> **Labels:** `wayfinder:grilling` `hitl` `finding:I` `finding:J`  
> **Status:** resolved (2026-07-27, owner interview) — see Decision below
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question

Two entangled premises on [MAP-phase2.md](../MAP-phase2.md) are false as stated. Both concern the same fact: two agents with write permission share one working directory.

### I — the agents already write into the repo outside `reports/` — this is not future risk, it happened

Premortem narrative **N5** describes this as a risk. It has already materialized:

- `research/sorting-comparison/` and `docs/research/quicksort-vs-mergesort/` were created **by the CLIs**, running under `--auto` / `--dangerously-skip-permissions`.
- Two different `benchmark.py` files with different SHA-256 hashes (`36547cd21cb5`, 6095 bytes, and `7e765538bd67`, 6181 bytes) — each agent wrote its own.
- One of them wrote into `docs/`, the **documentation** directory.
- `research/` and `docs/research/` were subsequently added to `.gitignore` (`.gitignore:26-27`) — which hides the symptom rather than stopping the writes.
- Also verified: child subprocesses **inherit the parent environment**, including `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY`.

[MAP-phase2.md](../MAP-phase2.md) currently gates isolation on watch mode ("not a blocker for manual MVP runs"). The evidence says isolation is needed **now**, on the manual path.

### J — "parallel dispatch is only a latency tweak" is false

[MAP-phase2.md](../MAP-phase2.md) asserts this twice (Notes: "Parallel `asyncio.gather` is a later latency tweak"; Not yet specified: "Parallel CLI dispatch (latency only)").

But both agents receive an **identical** prompt, both have write permission, and both share **one cwd**. They diverged into different directories by luck. `asyncio.gather` turns that luck into a **race on the same paths** — a correctness change, not a latency one. The recorded decision rests on a false premise.

### To settle

1. What isolation for the manual path, and how soon (container / firejail / restricted user / separate cwd per agent / env scrubbing)? Cheapest option that stops cross-writes and stops leaking API keys into free-tier CLIs.
2. Does each agent get its own working directory — which would dissolve J and also change how [P1H-T4](P1H-T4-report-contract-grilling.md) collects agent-written files?
3. Given the above, restate the parallel-dispatch entry on [MAP-phase2.md](../MAP-phase2.md) honestly: is it blocked on isolation rather than deferred as a tweak?

**Settle before [P2-T5](P2-T5-verifier-mvp-prototype.md)** — the follow-up loop re-runs both CLIs, doubling the exposure.

**Result:** an isolation decision applicable to manual runs today, plus a corrected statement of what parallel dispatch costs. Amend the Phase 2 map's Notes / Not yet specified accordingly.

## Decision (owner, 2026-07-27)

Answers to the three questions above, given by the owner in interview:

1. **Isolation for the manual path = separate cwd per agent + environment scrubbing.** Cheapest option that stops cross-writes and stops leaking `GOOGLE_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` into free-tier CLIs. Sandboxing (bubblewrap/firejail) and containers were considered and **not** taken now — an agent can still technically walk up the tree and write into the repo. That residual risk is accepted for manual runs and remains the gate for unattended watch mode.
2. **Yes — each agent gets its own working directory** (`reports/run-{timestamp}/kilocode/` and `.../opencode/`). This is also what [P1H-T4](P1H-T4-report-contract-grilling.md) collects from: artifact discovery scans **only** the agent's own cwd, never the shared `research/`.
3. **Parallel dispatch stays on.** With cwds split and the shared-directory scan removed, the original race in finding J is gone, and the run is roughly twice as fast. The stale *"latency only"* entry has been removed from [MAP-phase2.md](../MAP-phase2.md) *Not yet specified*; the Notes entry states what actually holds.

## Comments

- **2026-07-27 (Implementation):** Implemented per-agent CWD isolation (`run-{timestamp}/kilocode/` and `run-{timestamp}/opencode/`). Added environment scrubbing (`_clean_env`) in `agent_cli.py` removing API keys for free-tier CLIs. Parallelized CLI execution via `asyncio.gather`. Updated `MAP-phase2.md` notes. Unit tests added in `test_agent_cli.py` and `test_dispatcher.py`.
- **2026-07-27 (Process defect, then correction):** This ticket was labelled `hitl` and the map said *"Do not code them ahead of the decision"*. It was implemented and closed **without the owner interview** — and finding J was resolved by *enabling* the parallelism it warned about, which is exactly the kind of call that needed the owner. Review caught it; the interview was then held and its answers are recorded above. They confirm what was built, so no code changed.
- **2026-07-27 (E2E Verification - `--dir` isolation fix):** В `agent_cli.py` добавлен флаг `--dir <cwd>` в команды запуска Kilocode и Opencode CLI. Проведён повторный E2E-прогон `reports/run-20260727-171618/`:
  - Оба агента записали артефакты (`benchmark.py`, `summary.md`) строго внутрь своих изоляционных директорий `reports/run-20260727-171618/kilocode/` и `reports/run-20260727-171618/opencode/`. Корень репозитория полностью чист (`git status` не содержит необрабатываемого мусора).
  - Подсекция `## Обнаруженные артефакты на диске` в отчёте [`report-20260727-171618.md`](file:///home/fixedius/projects/research-pipeline/reports/run-20260727-171618/report-20260727-171618.md) появилась у ОБОИХ агентов (под `# Kilocode Output` и `# Opencode Output`).
  - Зафиксированы значения `wall_time_s` из `metrics.json`: Kilocode = `42.91 s`, Opencode = `60.34 s`.


