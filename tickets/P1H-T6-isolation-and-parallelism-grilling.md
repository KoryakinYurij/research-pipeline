# P1H-T6 — Grilling: CLI isolation now, and is parallel dispatch really a latency tweak?

> **Labels:** `wayfinder:grilling` `hitl` `finding:I` `finding:J`  
> **Status:** resolved (2026-07-27)  
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

## Comments
