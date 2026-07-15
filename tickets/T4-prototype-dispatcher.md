# T4 — Prototype: Dispatcher script

> **Labels:** `wayfinder:prototype` `hitl`
>
> **Blocked by:** T1 (Google AI Studio SDK), T2 (Kilocode & Opencode CLI), T3 (Project scaffolding), T5 (Model ID grilling)

## Question / Постановка

Написать Python-скрипт `src/dispatcher.py`, который реализует базовый пайплайн:

```
task.md → [kilocode] ─┐
                       ├→ Gemini cross-summary → report.md
task.md → [opencode]  ─┘
```

**Поведение:**

1. Читает `tasks/task.md`
2. Запускает `kilo run "<содержимое task>"` и `opencode run "<содержимое task>"` параллельно (или последовательно — проще для прототипа)
3. Сохраняет сырые ответы в `reports/kilocode-output.md` и `reports/opencode-output.md`
4. Вызывает Gemini 4 31B с системным промптом:
   > «Ты аналитический ассистент. Сравни два исследовательских отчёта. Выдели: (1) что общего, (2) в чём расходятся, (3) на что обратить внимание при проверке. Пиши на русском языке.»
5. Формирует `reports/report-{timestamp}.md`:
   ```markdown
   # Cross-Summary
   <результат Gemini>
   
   ---
   # Kilocode Output
   <сырой вывод kilocode>
   
   ---
   # Opencode Output
   <сырой вывод opencode>
   ```

**Для прототипа можно упростить:** запускать CLI последовательно, без параллельности. Главное — чтобы пайплайн проходил от начала до конца.

**Результат:** Работающий `uv run python src/dispatcher.py`, который можно запустить вручную.
