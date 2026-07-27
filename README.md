# Research Pipeline

Прототип Dispatcher: читает задачу, отправляет в Kilocode и Opencode, генерирует кросс-саммари через Gemma 4 31B.

## Установка

```bash
uv sync
```

Создать `.env` из `.env.example` и указать переменные окружения.

`uv run` не загружает `.env` автоматически — используй `--env-file`:

```bash
cp .env.example .env
# отредактировать .env
```

### Переменные окружения (`.env`)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `GOOGLE_API_KEY` | Ключ доступа к Google AI Studio API для Gemma 4 31B | *(обязательно для Gemma)* |
| `GEMMA_MODEL_ID` | Идентификатор модели Gemma | `gemma-4-31b-it` |
| `CLI_TIMEOUT` | Таймаут выполнения CLI-агентов (Kilocode / Opencode) в секундах | `120` |
| `GEMMA_TIMEOUT` | Таймаут генерации кросс-саммари Gemma в секундах | `60` |


## Запуск

```bash
uv run --env-file .env dispatcher
# или без кросс-саммари (если ключ не нужен):
uv run dispatcher
# или с произвольным task-файлом:
uv run dispatcher path/to/task.md
```

## Структура

- `src/research_pipeline/dispatcher.py` — основной скрипт
- `src/research_pipeline/clients/agent_cli.py` — вызов Kilocode/Opencode CLI
- `src/research_pipeline/clients/gemma.py` — кросс-саммари через Gemma 4 31B
- `tasks/` — входные task.md
- `reports/` — выходные report.md
- `tickets/` — wayfinder-тикеты
- `docs/research/` — материалы исследований
