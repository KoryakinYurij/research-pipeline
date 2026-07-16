"""Call Gemma 4 31B via Google AI Studio API for cross-summary generation.

Implemented in T4 (Prototype).
Key design decisions from T1:
- SDK: google-genai (google-generativeai is deprecated)
- Auth: GOOGLE_API_KEY env var (SDK reads automatically)
- Model ID: gemma-4-31B-it
- Context: 256K tokens — enough for two reports + summary, no chunking needed
"""

from research_pipeline.config import GEMMA_MODEL_ID, GOOGLE_API_KEY

SYSTEM_INSTRUCTION = """Ты аналитический ассистент. Сравни два исследовательских отчёта.
Выдели три аспекта:
1. **Что общего** — совпадающие факты, выводы, рекомендации.
2. **В чём расходятся** — противоречия, разные акценты, несогласованность.
3. **На что обратить внимание при проверке** — пробелы, сомнительные утверждения, что перепроверить.

Пиши на русском языке. Формат — Markdown."""


async def generate_cross_summary(kilo_output: str, opencode_output: str) -> str:
    """Send two agent outputs to Gemma 4 31B, return structured cross-summary in Russian.

    Returns: Markdown-formatted comparison with sections:
    (1) что общего, (2) расхождения, (3) на что обратить внимание.
    """
    if not GOOGLE_API_KEY:
        return (
            "_Кросс-саммари не сгенерировано: GOOGLE_API_KEY не задан._\n\n"
            "Добавьте ключ в `.env` и повторите запуск."
        )

    from google import genai  # noqa: PLC0415 — optional import at call site

    client = genai.Client()
    prompt = _build_prompt(kilo_output, opencode_output)

    response = await asyncio_to_thread(
        client.models.generate_content,
        model=GEMMA_MODEL_ID,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
        },
    )

    return response.text or "_Gemma вернула пустой ответ._"


def _build_prompt(kilo_output: str, opencode_output: str) -> str:
    """Assemble the user prompt for Gemma."""
    return (
        "## Отчёт Kilocode\n\n"
        f"{kilo_output}\n\n"
        "---\n\n"
        "## Отчёт Opencode\n\n"
        f"{opencode_output}"
    )


def asyncio_to_thread(func, *args, **kwargs):
    """Run a sync function in a thread pool executor — asyncio compatibility shim."""
    import asyncio

    return asyncio.get_running_loop().run_in_executor(
        None, lambda: func(*args, **kwargs)
    )
