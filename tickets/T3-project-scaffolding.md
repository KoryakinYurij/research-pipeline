# T3 — Task: Project scaffolding

> **Labels:** `wayfinder:task` `afk`
>
> **Assigned to:** fixedius (2026-07-15)
> **Status:** resolved ✅

## Question / Checklist

Подготовить структуру проекта для Dispatcher-прототипа:

- [x] Создать `projects/research-pipeline/` со структурой:
  ```
  research-pipeline/
  ├── MAP.md
  ├── tickets/
  ├── src/
  │   └── dispatcher.py      # будет создан в T4
  ├── tasks/                  # входные task.md файлы
  ├── reports/                # выходные report.md файлы
  ├── .env                    # GOOGLE_API_KEY (пользователь создаёт из .env.example)
  ├── pyproject.toml          # uv-проект
  └── README.md
  ```
- [x] Инициализировать uv-проект (`uv init`)
- [x] Добавить зависимости: `google-genai>=2.11.0` (SDK из T1)
- [x] Создать `.env.example` с комментариями какие переменные нужны
- [x] Создать `README.md` с кратким описанием проекта и инструкцией по запуску

**Результат:** Готовая структура проекта, `uv run` работает.

---

## Resolution

Проект инициализирован на VPS (`/home/fixedius/projects/research-pipeline`).

**Выполнено:**
- Структура: `src/`, `tasks/`, `reports/`, `tickets/`, `docs/research/`
- `uv init --name research-pipeline --python 3.12`
- Зависимость: `google-genai==2.11.0`
- `.env.example` — содержит `GOOGLE_API_KEY=your_key_here`
- `README.md` — описание, установка (`uv sync`), запуск (`uv run python src/dispatcher.py`)
- `uv run python -c "import google.genai"` — работает

**Примечание:** на Windows `UV_PYTHON` нужно указывать явно из-за конфликта с Hermes-venv; на VPS не требуется.
