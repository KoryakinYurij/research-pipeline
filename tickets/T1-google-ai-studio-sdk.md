# T1 — Research: Google AI Studio Python SDK для Gemma 4 31B

> **Labels:** `wayfinder:research` `afk`
> **Status:** resolved ✅

## Question

Как вызывать Gemma 4 31B через Google AI Studio API из Python? Нужно выяснить:

1. Какой **model ID** у Gemma 4 31B?
2. Какой **Python SDK** использовать? `google-generativeai`? `google-genai`?
3. Как **аутентифицироваться**? `GOOGLE_API_KEY` env var? Другой механизм?
4. Как передать **системный промпт** (инструкция: «ты делаешь кросс-саммари двух отчётов») + **пользовательский контент** (два отчёта)?
5. Есть ли **лимиты** на размер запроса (токены)? Может понадобиться разбивать большие отчёты.
6. Какой формат ответа — plain text или можно запросить структурированный JSON/Markdown?

**Результат:** Markdown-файл с примерами кода и ссылками на документацию.

---

## Resolution

**Создан:** [`docs/research/T1-google-ai-studio-sdk-findings.md`](../docs/research/T1-google-ai-studio-sdk-findings.md)

**Ключевые выводы:**

1. **Model ID:** `gemma-4-31B-it` — модель реально существует, выпущена Google DeepMind 2 апреля 2026. 31B параметров, 256K контекст, доступна через Google AI Studio API.
2. **SDK:** `google-genai` (новый унифицированный SDK). Старый `google-generativeai` — deprecated.
3. **Аутентификация:** `GOOGLE_API_KEY` env var, SDK подхватывает автоматически.
4. **Системный промпт:** через `system_instruction` в конфиге `generate_content()`.
5. **Лимиты:** 256K токенов контекст — достаточно для двух отчётов + саммари, разбиение не требуется.
6. **Формат ответа:** text/Markdown по умолчанию, можно JSON через Pydantic-схему. Нативная поддержка structured output.

