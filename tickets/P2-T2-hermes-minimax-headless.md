# P2-T2 — Research: Hermes CLI + Minimax M3 headless

> **Labels:** `wayfinder:research` `afk`  
> **Status:** open  
> **Blocked by:** —  
> **Map:** [MAP-phase2.md](../MAP-phase2.md)

## Question

How do we call **Minimax M3 via Hermes CLI** non-interactively from Python (same class of problem as T2 for Kilo/Opencode)?

Determine:

1. Hermes version on this machine; invoke command for one-shot prompt → stdout.
2. How to select **Minimax M3** (model id / config / flags).
3. Headless requirements: stdin, TTY, permissions flags, timeouts, auth/env.
4. Output format: plain text vs JSON/NDJSON; how to request **structured JSON** for verdict schema.
5. Failure modes: missing CLI, auth fail, model not found, hang — soft-fail pattern like `agent_cli.py`.
6. Working example command + recommended Python wrapper sketch (do not implement full Verifier here).

**Result:** Markdown findings under `docs/research/` (e.g. `P2-T2-hermes-minimax-findings.md`), with copy-pasteable commands. Note gitignore on `docs/research/` — `git add -f` if needed.

## Comments
