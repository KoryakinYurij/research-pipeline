# HANDOFF — T4 Dispatcher Prototype (2026-07-16)

## Что сделано в этой сессии

Дописан и отлажен `agent_cli.py` — модуль для вызова Kilocode и Opencode в headless-режиме из Python (asyncio).
Дописан `dispatcher.py` — добавлен `flush=True` на все print'ы (иначе вывод теряется без TTY).

## Текущий статус

- ✅ `agent_cli.py` — **работает**. Тест `run_kilocode("2+2?")` возвращает `{'text': '4', ...}`.
- ✅ `dispatcher.py` — код корректен, ruff чисто.
- ✅ Полный прогон пайплайна — **верифицирован** (2026-07-16): smoke-задача «Ответь одним словом: pong» → Kilocode: `pong`, Opencode: `pong` → `report-20260716-055921.md` создан. Gemma-саммари пропущена (нет `GOOGLE_API_KEY`) — ожидаемо.

## Ключевые архитектурные решения (финал)

### agent_cli.py

```python
# Прямой вызов CLI через asyncio.create_subprocess_exec (без shell!)
# stdin=DEVNULL — КРИТИЧНО: оба CLI виснут без этого
# NDJSON-структура: {"type":"text", "part":{"text":"..."}}
#   └─ текст в part.text, а НЕ в корне obj.text!
# Модели: kilo/kilo-auto/free и opencode/deepseek-v4-flash-free
# stderr читается конкурентно (asyncio.create_task) — иначе deadlock
# Общий таймаут через asyncio.timeout()
```

### dispatcher.py

```python
# Все print() с flush=True — без этого вывод буферизируется и теряется при timeout
# Последовательное выполнение: kilo → opencode → gemma cross-summary
```

## Проверенные факты

### Что работает (протестировано в этой сессии)

```bash
# Оба CLI работают с --format json при < /dev/null (stdin=DEVNULL в коде)
echo '' | timeout 30 kilo run --auto --format json "2+2?" < /dev/null
# → {"type":"text","part":{"text":"4",...}}

echo '' | timeout 30 opencode run --dangerously-skip-permissions --format json "2+2?" < /dev/null
# → {"type":"text","part":{"text":"4",...}}

# С явным указанием free-моделей — тоже работает
kilo run --auto --format json --model kilo/kilo-auto/free "2+2?" < /dev/null
opencode run --dangerously-skip-permissions --format json -m opencode/deepseek-v4-flash-free "2+2?" < /dev/null
```

### Модели

| CLI | Free-модель | Примечание |
|-----|------------|------------|
| Kilocode 7.3.1 | `kilo/kilo-auto/free` | Из конфига `~/.config/kilo/kilo.jsonc` |
| Opencode 1.17.11 | `opencode/deepseek-v4-flash-free` | Из `opencode models`, **не** `deepseek/deepseek-v4-flash-free` |
| Opencode (альт.) | `opencode/hy3-free`, `opencode/mimo-v2.5-free` | Другие free-модели |

### NDJSON-структура (реальная, проверена)

```json
{"type":"step_start","part":{"id":"...","type":"step-start",...}}
{"type":"text","part":{"id":"...","type":"text","text":"4",...}}     ← текст ЗДЕСЬ
{"type":"step_finish","part":{"id":"...","type":"step-finish",...}}
```

**Важно:** текст в `part.text`, а не в корневом `text`! Это отличает от структуры `{"type":"text","text":"..."}` которую предлагают некоторые источники.

### Opencode: флаги

- `--dangerously-skip-permissions` — **правильный** флаг для headless (не `--auto`, его нет в v1.17.11)
- `--format json` — работает, выдаёт NDJSON
- `-m provider/model` — указание модели (не `--model`)

## Verification status (2026-07-16 smoke test)

**✅ E2E verified:** `uv run python -u -m research_pipeline tasks/smoke.md`

- Kilocode: `pong` (4 chars, exit=0)
- Opencode: `pong` (4 chars, exit=0)
- Cross-summary: skipped (no `GOOGLE_API_KEY`) — expected, code handles gracefully
- Report: `reports/report-20260716-055921.md` created

### Причина прошлых неудач

Basher-агент нестабилен с долгими командами — проблема Layer B (verification harness), не кода. Для успешного прогона нужен либо:
- Прямой запуск (без nohup) с таймаутом ≥90s
- SSH/человек

## Что НЕ делать

- ❌ Не использовать `script -q -c` — проверено, это тупиковый путь (проблемы с shell-экранированием многострочных промптов).
- ❌ Не использовать `--model kilo-auto/free` без префикса `kilo/` — `ProviderModelNotFoundError`.
- ❌ Не использовать `deepseek/deepseek-v4-flash-free` без префикса `opencode/` — `UnknownError`.
- ❌ Не ставить таймауты >60s на тесты — если работает, то быстро.
- ❌ Не передавать prompt через файл (`-f`) — это «прикрепить файл к сообщению», а не «прочитать prompt из файла».

## Файлы, изменённые в этой сессии

- `src/research_pipeline/clients/agent_cli.py` — полностью переписан
- `src/research_pipeline/dispatcher.py` — добавлен `flush=True` во все `print()`

---

# HANDOFF — P1 Hygiene (2026-07-16, follow-up session)

## Что сделано

### Verification gap closed
E2E smoke-прогон: `uv run python -u -m research_pipeline tasks/smoke.md` → оба CLI `pong`, `report-*.md` создан. Проблема HANDOFF была в Layer B (basher), не в коде.

### P1 Hygiene fixes
- `agent_cli.py`: `FileNotFoundError` soft-fail на отсутствующий CLI, `start_new_session=True` + `os.killpg` на таймаут (нет orphan-процессов), `_parse_ndjson_text()` — чистая функция для тестирования
- `README.md`: entry point `uv run dispatcher`, `--env-file .env`, актуальная структура
- `tests/test_agent_cli.py`: 11 unit-тестов NDJSON-парсинга (все green)
- `MAP.md`: T4 verified, P1 hygiene documented

### Dev-команды
```bash
uv run ruff check src/ tests/   # clean
uv run pytest -v tests/          # 11 passed
uv run dispatcher                # entry point (без --env-file если ключ не нужен)
```

---

# HANDOFF — Gemma 4 31B E2E Verification (2026-07-22)

## Что сделано

### E2E Verification with Gemma 4 31B
- Добавлен шаблон и файл `.env` с `GOOGLE_API_KEY`.
- Исправлено имя модели в `src/research_pipeline/config.py`: `gemma-4-31b-it` (в нижнем регистре, как того требует API Google AI Studio).
- Запущен полный E2E прогон с генерацией кросс-саммари: `uv run --env-file .env python -u -m research_pipeline tasks/smoke.md`.
- Результат: Kilocode (`pong`), Opencode (`pong`), Gemma 4 31B успешно создала аналитическое сравнение на русском языке в `reports/report-20260722-102854.md`.

### Изменённые файлы
- `src/research_pipeline/config.py`: исправление `GEMMA_MODEL_ID` на `gemma-4-31b-it`
- `tasks/smoke.md`: создан быстрый тест-кейс
- `.env.example`: обновлен с понятной инструкцией

