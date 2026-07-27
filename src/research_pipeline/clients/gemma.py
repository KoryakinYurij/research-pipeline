"""Call Gemma 4 31B via Google AI Studio API for cross-summary generation.

Implemented in T4 (Prototype).
Key design decisions from T1:
- SDK: google-genai (google-generativeai is deprecated)
- Auth: GOOGLE_API_KEY env var (SDK reads automatically)
- Model ID: gemma-4-31b-it (lowercase "b" — the API rejects gemma-4-31B-it)
- Context: 256K tokens — enough for two reports + summary, no chunking needed
"""

import asyncio

from research_pipeline.config import GEMMA_MODEL_ID, GEMMA_TIMEOUT, GOOGLE_API_KEY

SYSTEM_INSTRUCTION = """Ты аналитический ассистент. Сравни два исследовательских отчёта двух независимых агентов относительно исходного задания (task.md).
Выдели три аспекта:
1. **Покрытие задания и что общего** — насколько полно выполнены требования task.md, какие совпадающие факты, выводы и рекомендации получили оба агента.
2. **В чём расходятся** — противоречия между агентами, разные акценты, несогласованность данных.
3. **На что обратить внимание при проверке** — пробелы относительно task.md, недостоверные утверждения, что необходимо перепроверить.

Пиши на русском языке. Формат — Markdown."""


async def generate_cross_summary(
    task_content: str,
    kilo_output: str,
    opencode_output: str,
    timeout: int = GEMMA_TIMEOUT,
) -> str:
    """Send task.md and two agent outputs to Gemma 4 31B, return structured cross-summary in Russian.

    Returns: Markdown-formatted comparison with sections:
    (1) покрытие задания и что общего, (2) расхождения, (3) на что обратить внимание.
    """
    if not GOOGLE_API_KEY:
        return (
            "_Кросс-саммари не сгенерировано: GOOGLE_API_KEY не задан._\n\n"
            "Добавьте ключ в `.env` и повторите запуск."
        )

    from google import genai  # noqa: PLC0415 — optional import at call site

    client = genai.Client()
    prompt = _build_prompt(task_content, kilo_output, opencode_output)

    try:
        async with asyncio.timeout(timeout):
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMMA_MODEL_ID,
                contents=prompt,
                config={
                    "system_instruction": SYSTEM_INSTRUCTION,
                },
            )
    except TimeoutError:
        raise TimeoutError(f"Gemma call timed out after {timeout}s")

    return response.text or "_Gemma вернула пустой ответ._"


def _build_prompt(task_content: str, kilo_output: str, opencode_output: str) -> str:
    """Assemble the user prompt for Gemma."""
    return (
        "## Исходное задание (task.md)\n\n"
        f"{task_content}\n\n"
        "---\n\n"
        "## Отчёт Kilocode\n\n"
        f"{kilo_output}\n\n"
        "---\n\n"
        "## Отчёт Opencode\n\n"
        f"{opencode_output}"
    )

