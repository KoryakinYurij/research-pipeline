# T5 — Grilling: Уточнить model ID для кросс-саммари

> **Labels:** `wayfinder:grilling` `hitl`
> **Status:** resolved ✅

## Question

~~Уточнить у пользователя, какую модель он имел в виду, поскольку «Gemini 4 31B» не был найден при первом исследовании.~~

## Resolution

При повторном исследовании выяснилось: пользователь имел в виду **Gemma 4 31B** (не Gemini!). 

- **Gemma 4 31B** — реальная модель Google DeepMind, выпущена 2 апреля 2026.
- **Model ID:** `gemma-4-31B-it`
- **31B параметров**, dense-архитектура, **256K контекст**
- **Доступна через Google AI Studio API** (тот же SDK `google-genai`)
- Поддерживает function-calling, structured JSON, system instructions

Детали: [T1 findings](../docs/research/T1-google-ai-studio-sdk-findings.md)
