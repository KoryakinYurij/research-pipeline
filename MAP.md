# Research Pipeline — Wayfinder Map

> **Label:** `wayfinder:map`

## Destination

Работающий прототип **Dispatcher** на Python: читает задачу из `task.md` → отправляет в Kilocode CLI и Opencode CLI → сохраняет оба сырых отчёта → через Gemma 4 31B (Google AI Studio) генерирует кросс-саммари (общее / различия / на что обратить внимание) → формирует финальный `report.md`.

**✅ Destination достигнут (2026-07-16).** Дальнейшие шаги:
- **Verifier (Phase 2)** — следующая wayfinder-карта: проверка качества отчётов, петля доисследования.
- **Level 2 serve** — тикет в Not yet specified: замена subprocess на `kilo serve`/`opencode serve` + HTTP.
- **Composer** — отдельный агент (Hermes + Minimax M3), генерирует `task.md`. Вне скоупа этой карты.

## Notes

- **Язык:** Python 3.12 с `uv` для управления зависимостями
- **Структура:** `src-layout` (`src/research_pipeline/`), модули: `config.py`, `dispatcher.py`, `clients/agent_cli.py`, `clients/gemma.py`
- **Точка входа:** `uv run dispatcher` (или `python -m research_pipeline`)
- **Dev-инструменты:** `ruff` (format + lint), `pytest` (заготовка)
- **Установленные CLI:** Kilocode 7.3.1, Opencode 1.17.11, Hermes 0.18.0
- **Модель для саммари:** Gemma 4 31B через Google AI Studio API (ключ есть у пользователя)
- **Модель для Verifier'а (Phase 2):** Minimax M3 через Hermes
- **Запуск:** вручную, позже автоматизируем
- **Задачи:** генерируются Composer'ом (отдельный агент, вне скоупа)
- **Скиллы для консультации:** oacp (если понадобится координация агентов), prototype

## Decisions so far

- [T1 — Research: Google AI Studio Python SDK для Gemma 4 31B](tickets/T1-google-ai-studio-sdk.md) — используем `google-genai`, аутентификация через `GOOGLE_API_KEY`, системный промпт через `system_instruction`. Model ID: `gemma-4-31B-it`. 256K контекст, нативный structured output, function-calling.

- [T5 — Grilling: Уточнить model ID](tickets/T5-model-id-grilling.md) — подтверждено: Gemma 4 31B (не Gemini), model ID `gemma-4-31B-it`, доступна через Google AI Studio API.

- [T2 — Research: Kilocode & Opencode CLI в неинтерактивном режиме](tickets/T2-kilocode-opencode-cli.md) — основной подход: `--format json` (headless-режим, TTY не нужен, NDJSON-стрим). Production: `opencode serve` / `kilo serve`. `script`/`pty` — deprecated. Opencode: `--dangerously-skip-permissions`, дефолт `opencode/hy3-free`. Kilo: `--auto`, дефолт `kilo-auto/free`. Gemma 4 31B недоступна ни в одном из CLI.

- [T3 — Task: Project scaffolding](tickets/T3-project-scaffolding.md) — проект на VPS, uv-окружение, `src-layout` (`src/research_pipeline/`). Модули: `config.py` (os.getenv, без pydantic-settings), `clients/agent_cli.py`, `clients/gemma.py`. Точка входа: `uv run dispatcher`. Dev: `ruff`, `pytest`. `pydantic-settings` сознательно отклонён как оверкилл.

- [T4 — Prototype: Dispatcher](tickets/T4-prototype-dispatcher.md) — ✅ E2E verified (2026-07-16, Gemma verified 2026-07-22). Smoke-тест «pong»: оба CLI и Gemma 4 31B (`gemma-4-31b-it`) отвечают корректно, `report-*.md` с кросс-саммари создаётся. P1 hygiene: soft-fail на отсутствующий CLI (`FileNotFoundError`), process-group kill на таймаут (`os.killpg`), README fix (entry point + `--env-file`), unit-тесты NDJSON-парсинга (11 тестов).

## Not yet specified

- **Формат `task.md`** — будет определён когда появится Composer. Dispatcher'у достаточно читать содержимое как текст.
- **Ретраи и degraded mode** — что делать если один CLI упал, а второй отработал. Soft-fail на `FileNotFoundError` уже есть; ретраи и fallback-стратегия — позже.
- **Дизайн Verifier'а** — критерии качества, петля доисследования, формат финального документа. Исследовать в Phase 2.
- **Автоматизация** — watch-режим, OACP-интеграция. После прототипа.
- **Level 2 (serve + HTTP)** — production-путь через `kilo serve` / `opencode serve` + OpenAPI. Не блокирует T4; отдельный тикет Phase 2.

## Out of scope

- **Composer (Hermes + Minimax M3)** — отдельный агент, который будет создавать задачи. Не входит в этот research pipeline.
- **Verifier (Phase 2)** — будет отдельной картой после завершения Dispatcher-прототипа.
- **`pydantic-settings`** — предложен в ревью T3 как SOTA, отклонён: оверкилл для прототипа с 3 env-переменными. Подробное обоснование — в [T3 resolution](tickets/T3-project-scaffolding.md): scale mismatch (3 значения vs библиотека для сложных конфигов), читаемость плоских констант лучше, Google SDK сам валидирует ключ при вызове, соблюдение принципа «no abstractions for single-use code».
