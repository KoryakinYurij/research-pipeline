# P1H-T7 — Task: Doc/code canon and hygiene sweep

> **Labels:** `wayfinder:task` `afk` `finding:P` `finding:R`  
> **Status:** resolved (2026-07-27)  
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question / work

Small verified items where doc, config or test disagrees with the code. Sweep them together.

Findings **N** (model-ID canon), **O** (Opencode default model) and **Q** (Phase 2 status wording) were already corrected in place while charting — see [MAP-phase1-hardening.md](../MAP-phase1-hardening.md) Notes. They are **not** part of this ticket.

### P — the research canon lives behind `.gitignore`

`.gitignore:26-27` excludes `docs/research/` and `research/`. Three findings files reached git only via `git add -f`.

Consequence: the planned `P2-T2-hermes-minimax-findings.md` will **not** reach git by default, and [P2-T2](P2-T2-hermes-minimax-headless.md) honestly warns "`git add -f` if needed" instead of removing the rule. A knowledge-loss trap baked into config.

Work: take `docs/research/` out of `.gitignore` (the canon belongs in git) while keeping `research/` — the agents' own scratch output — ignored. Then `git add` the findings files that are currently only force-added.

While there: `docs/research/T1-google-ai-studio-sdk-findings.md` still carries the wrong `gemma-4-31B-it` in four places (lines 8, 16, 59, 107) including two code samples. It was left out of the charting-time canon fix precisely because it sits behind `.gitignore` — fix it once the file is tracked.

Related, and for the owner rather than this ticket: [`docs/premortem-long-run.md`](../docs/premortem-long-run.md) and the [MAP-phase2.md](../MAP-phase2.md) edits are **uncommitted** as of 2026-07-27.

### R — smaller items

- **`gemma.py:62-68` reinvents `asyncio.to_thread`.** A hand-rolled `asyncio_to_thread` shim, while `asyncio.to_thread` is verified present in Python 3.12. This violates T3's own stated rationale ("no abstractions for single-use code") — the same argument used to reject `pydantic-settings`. Replace with the stdlib call. Note this touches the same lines as the timeout work in [P1H-T3](P1H-T3-bound-prompt-and-gemma-call.md); do whichever lands second on top of the other.
- **[`README.md`](../README.md) documents one env var of three.** It mentions `GOOGLE_API_KEY` only; `CLI_TIMEOUT` and `GEMMA_MODEL_ID` (`config.py:13,16`) are absent — while the `pydantic-settings` rejection was argued precisely on "there are only three env vars". Document all three. (README is Russian — match it.)
- **`tests/test_agent_cli.py::test_flat_text_property` enshrines fragility.** It asserts that the flat `{"type":"text","text":...}` shape returns `None`. On an upstream schema change that assertion keeps passing while the pipeline yields **empty text with `exit 0`** — which finding E shows is counted as success. Decide whether the test should instead pin the behaviour we *want* (loud failure on an unrecognized shape).
- **[P2-T4](P2-T4-layer-a-gates.md) label mismatch.** Labelled `hitl`, while [`HANDOFF.md`](../HANDOFF.md) calls it "prototype, AFK-friendly". Matters for what can be handed to an unattended worker — pick one and make the two agree.

**Result:** `docs/research/` tracked in git; three env vars documented; the shim replaced; the test question and the P2-T4 label settled.

## Comments
