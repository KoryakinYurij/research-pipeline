# Research Pipeline

Прототип Dispatcher: читает задачу, отправляет в Kilocode и Opencode, генерирует кросс-саммари через Gemma 4 31B.

## Установка

```bash
uv sync
```

Создать `.env` из `.env.example` и указать `GOOGLE_API_KEY`.

## Запуск

```bash
uv run python src/dispatcher.py
```

## Структура

- `src/dispatcher.py` — основной скрипт
- `tasks/` — входные task.md
- `reports/` — выходные report.md
- `tickets/` — wayfinder-тикеты
- `docs/research/` — материалы исследований
