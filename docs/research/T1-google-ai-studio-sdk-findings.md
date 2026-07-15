# T1 Research Findings: Google AI Studio Python SDK + Gemma 4 31B

> **Date:** 2026-07-13
> **Updated:** 2026-07-13 (исправлено: Gemma 4 31B вместо Gemini)

## Q1: Model ID для «Gemma 4 31B»

**Вывод:** Модель существует. Это `gemma-4-31B-it`.

- **Gemma 4 31B** — dense-модель на 31B параметров, выпущена Google DeepMind **2 апреля 2026**.
- **Лицензия:** Apache 2.0 (open weights).
- **Контекст:** 256K токенов.
- **Мультимодальность:** текст + изображения + видео.
- **Агентные фичи:** function-calling, structured JSON output, system instructions.
- **Доступна через Google AI Studio API** — можно вызывать так же, как Gemini-модели.
- **Model ID:** `gemma-4-31B-it`

Веса также доступны на Hugging Face (`google/gemma-4-31B`), Kaggle, и через Ollama/llama.cpp для локального запуска.

## Q2: Python SDK

**Вывод:** `google-genai` (новый унифицированный SDK).

Старый `google-generativeai` — **deprecated**, End-of-Life 30 ноября 2025.

```bash
uv add google-genai
```

```python
from google import genai
```

Документация: https://googleapis.github.io/python-genai/

## Q3: Аутентификация

**Вывод:** `GOOGLE_API_KEY` — переменная окружения. SDK подхватывает автоматически.

```bash
export GOOGLE_API_KEY='your_key_here'
```

```python
from google import genai
client = genai.Client()  # авто из env
# или явно:
client = genai.Client(api_key='...')
```

Получить ключ: https://aistudio.google.com/apikey

## Q4: Системный промпт + пользовательский контент

**Вывод:** Системная инструкция передаётся через `system_instruction` в конфиге.

```python
response = client.models.generate_content(
    model='gemma-4-31B-it',
    contents=f"""Сравни два исследовательских отчёта:

=== ОТЧЁТ 1 (Kilocode) ===
{kilocode_output}

=== ОТЧЁТ 2 (Opencode) ===
{opencode_output}
""",
    config={
        "system_instruction": (
            "Ты аналитический ассистент. Сравни два исследовательских отчёта. "
            "Выдели: (1) что общего, (2) в чём расходятся, "
            "(3) на что обратить внимание при проверке. Пиши на русском языке."
        ),
    },
)
print(response.text)
```

## Q5: Лимиты токенов

Gemma 4 31B: **256K токенов контекст**. Этого более чем достаточно для двух отчётов + саммари. Разбиение на чанки не требуется.

**Rate limits free tier:** точные цифры не раскрываются, «щедрые но с ограничениями». Данные могут использоваться для улучшения моделей.

## Q6: Формат ответа

По умолчанию — plain text/Markdown. Можно запросить structured JSON:

```python
config={
    "response_mime_type": "application/json",
    "response_schema": MyPydanticModel,  # опционально
}
```

Gemma 4 31B нативно поддерживает structured JSON output.

## Итого: Минимальный рабочий пример

```python
import os
from google import genai

client = genai.Client()  # GOOGLE_API_KEY из env

response = client.models.generate_content(
    model='gemma-4-31B-it',
    contents="Сравни отчёт A и отчёт B...",
    config={
        "system_instruction": "Ты аналитический ассистент. Пиши на русском.",
    },
)
print(response.text)
```

## Источники

- [Google DeepMind: Gemma 4 Announcement (April 2, 2026)](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)
- [Google AI for Developers: Gemma 4 Model Overview](https://ai.google.dev/gemma/docs/core)
- [Hugging Face: google/gemma-4-31B](https://huggingface.co/google/gemma-4-31B)
