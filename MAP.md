# Research Pipeline — Wayfinder Map

> **Label:** `wayfinder:map`

## Destination

Работающий прототип **Dispatcher** на Python: читает задачу из `task.md` → отправляет в Kilocode CLI и Opencode CLI → сохраняет оба сырых отчёта → через Gemma 4 31B (Google AI Studio) генерирует кросс-саммари (общее / различия / на что обратить внимание) → формирует финальный `report.md`.

**Verifier** — следующим этапом (Phase 2), вне скоупа этой карты.

## Notes

- **Язык:** Python 3.12 с `uv` для управления зависимостями
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

- [T3 — Task: Project scaffolding](tickets/T3-project-scaffolding.md) — проект на VPS, uv-окружение: `google-genai==2.11.0`, Python 3.12. Структура: `src/`, `tasks/`, `reports/`. `uv sync` проходит, `uv run` работает.

## Not yet specified

- **Формат `task.md`** — будет определён когда появится Composer. Dispatcher'у достаточно читать содержимое как текст.
- **Стратегия обработки ошибок** — таймауты, ретраи, что делать если один из CLI упал. Уточнится на прототипе.
- **Дизайн Verifier'а** — критерии качества, петля доисследования, формат финального документа. Исследовать в Phase 2.
- **Автоматизация** — watch-режим, OACP-интеграция. После прототипа.

## Out of scope

- **Composer (Hermes + Minimax M3)** — отдельный агент, который будет создавать задачи. Не входит в этот research pipeline.
- **Verifier (Phase 2)** — будет отдельной картой после завершения Dispatcher-прототипа.
