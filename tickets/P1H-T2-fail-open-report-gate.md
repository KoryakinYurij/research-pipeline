# P1H-T2 — Task: Close the fail-open report hole

> **Labels:** `wayfinder:task` `afk` `finding:D` `finding:E`  
> **Status:** resolved (2026-07-27)  
> **Blocked by:** —  
> **Map:** [MAP-phase1-hardening.md](../MAP-phase1-hardening.md)

## Question / work

The pipeline is **fail-open**: a `report-*.md` is written even when both agents produced nothing. This is observed behaviour, not a hypothesis — the proof is committed in this repo.

### D — a report is always written, even on total failure

- `dispatcher.py:69-88` writes `report-*.md` **unconditionally**.
- `dispatcher.py:56-57` substitutes `_Пустой ответ_` for empty output, so emptiness looks like content.
- `dispatcher.py:58` still spends a Gemma call on that emptiness.

Evidence in-repo: [`reports/report-20260722-102812.md`](../reports/report-20260722-102812.md) has **both** CLIs at `exit_code: -1`, no text, and Gemma replying that it cannot compare emptiness — i.e. a file that looks like a result. Five minutes earlier, [`reports/report-20260722-102338.md`](../reports/report-20260722-102338.md) ran the **same** `task.md` and succeeded. So `CLI_TIMEOUT=120` (`config.py:16`) sits right on the boundary of a real research task, and runs flap across it.

### E — `ok` is derived from the exit code alone

- `agent_cli.py:130` — `"ok": (proc.returncode == 0)`. Empty output with `exit 0` counts as success.
- `agent_cli.py:128` — `"exit_code": proc.returncode or 0` maps `None` → `0`, so a failed run can print `exit_code: 0` in the report.

Minor next to D, but it is exactly why an intake gate must be mandatory rather than advisory.

### The work

If **both** agents are empty or failed: do **not** write `report-*.md`, and do **not** call Gemma. Fail loudly instead.

This *is* Layer A, applied at intake rather than post hoc. A gate that runs after the artifact already exists on disk does not stop anyone from reading it. Coordinate the shape with [P2-T4 — Layer A programmatic gates](P2-T4-layer-a-gates.md) so the two do not diverge into separate notions of "empty"; the map's standing rule that a **one**-CLI success is a *partial* report stays owned by Phase 2.

**Result:** a run where both CLIs fail produces no report and a non-zero exit; a partial run still produces a report but is flagged. Unit-tested on the pure decision function.

## Comments

- **2026-07-27 (Implementation):** Added `has_agent_outputs` intake gate in `dispatcher.py`. Requires `exit_code == 0` and non-empty text for both agents. Aborts pipeline execution with `RuntimeError` and `sys.exit(1)` when both agents fail or output empty text, preventing Gemma invocation and report generation. Unit tests added in `test_dispatcher.py`.
- **2026-07-27 (E2E Measurement):** Зафиксирован замер первого E2E-прогона: Kilocode 65.6 с, Opencode 97.2 с при CLI_TIMEOUT=120 — 81% бюджета на демо-задаче. Значение CLI_TIMEOUT остаётся без изменений (решение владельца).
- **2026-07-27 (Text preservation on timeout & CLI_TIMEOUT increase):**
  - **Дефект потери текста:** В `agent_cli.py` при возникновении `TimeoutError` и `ValueError` ранее возвращалось `"text": ""`, что приводило к полной потере накопленного ответа агента. Починено: возвращается накопленный фрагмент `"text": "".join(text_parts)`, а в `stderr` добавляется пометка усечения по таймауту `(truncated)`. При этом `ok` остаётся `False`, решение о валидности принимает intake-gate.
  - **Увеличение таймаута:** Значение `CLI_TIMEOUT` в `config.py` поднято со 120 до 600 с (решение владельца). Обоснование: разброс времени на идентичной задаче до 1.5× (Kilocode 65.6с → 42.9с, Opencode 97.2с → 60.3с), а демо-задача съедала 81% старого бюджета.



