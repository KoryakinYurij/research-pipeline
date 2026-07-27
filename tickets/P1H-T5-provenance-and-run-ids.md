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

- **2026-07-27 (Implementation):** Implemented run scoping (`reports/run-{timestamp}/`) for raw outputs, `metrics.json`, and `report-{timestamp}.md`. Implemented `_parse_ndjson_metrics` and `wall_time_s` tracking using `time.monotonic()` in `agent_cli.py` and `dispatcher.py`. Unit tests added in `test_agent_cli.py` and `test_dispatcher.py`.
- **2026-07-27 (E2E Verification):** Проведён реальный E2E-прогон пайплайна с созданием файлов на диске (задача в `tasks/task.md`: сравнение RLE и Huffman).
  - `reports/run-20260727-170708/`: создана с подпапками `kilocode/` и `opencode/`.
  - Изоляция CWD & `git status`: Kilocode записал файлы строго в `reports/run-20260727-170708/kilocode/` (`benchmark.py`, `summary.md`). Opencode проигнорировал CWD и намусорил в корень репозитория (`benchmark.py`, `summary.md`, `research-benchmarks/` отображаются не отслеживаемыми в `git status`).
  - Секция `## Обнаруженные артефакты на диске`: В `report-20260727-170708.md` подсекция присутствует под `# Kilocode Output` с полным содержимым `benchmark.py` и `summary.md`. Артефакты Opencode не попали, т.к. `_enrich_output_with_artifacts` ищет строго внутри `opencode_cwd`.
  - `metrics.json`: создан (18.9 KiB). Массивы `events` непустые (по 10 событий `step_finish` у Kilocode и Opencode) с реальными данными о токенах (`total`, `input`, `output`, `reasoning`, `cache`), `wall_time_s` (65.63s / 97.20s), `sessionID` и snapshot hashes.
  - Покрытие `task.md`: первая секция cross-summary от Gemma имеет заголовок `### 1. Покрытие задания и что общего`.
  - Утечка ключей: `GOOGLE_API_KEY` не утекал в дочерние процессы (вычищается `_clean_env()`), греп по отчётам совпадений не обнаружил.


