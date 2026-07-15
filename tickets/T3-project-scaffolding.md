# T3 — Task: Project scaffolding

> **Labels:** `wayfinder:task` `afk`
>
> **Assigned to:** fixedius (2026-07-15)
> **Status:** 🔄 reopened — post-review improvements applied 2026-07-15

## Question / Checklist

Подготовить структуру проекта для Dispatcher-прототипа:

- [x] Создать `projects/research-pipeline/` со структурой
- [x] Инициализировать uv-проект (`uv init`)
- [x] Добавить зависимости: `google-genai>=2.11.0`
- [x] Создать `.env.example`
- [x] Создать `README.md`

**Post-review additions (2026-07-15):**

- [x] Переход на `src-layout`: `src/research_pipeline/` как устанавливаемый пакет
- [x] Модуляризация: `config.py`, `dispatcher.py`, `clients/agent_cli.py`, `clients/gemma.py`
- [x] `pyproject.toml`: `[project.scripts]` (entry point `dispatcher`), `[build-system]` (hatchling)
- [x] Dev-зависимости: `ruff>=0.3.0`, `pytest>=8.0.0`
- [x] `tests/` — пустая заготовка под будущие тесты

**Сознательно отклонено:**

- **`pydantic-settings`** — предложен внешним ревьюером как «SOTA 2026». Отклонён по четырём причинам:
  1. **Scale mismatch.** `pydantic-settings` тянет pydantic как транзитивную зависимость. Библиотека рассчитана на десятки настроек со сложной валидацией, вложенными конфигами и несколькими источниками (env, file, vault). Здесь — 3 переменных: `GOOGLE_API_KEY`, `GEMMA_MODEL_ID`, `CLI_TIMEOUT`.
  2. **Читаемость.** Плоские `os.getenv`-константы на уровне модуля видны за один взгляд. Класс `Settings(BaseSettings)` требует понимания модели, `Config`-класса, env-префиксов — лишний когнитивный налог для читающего код.
  3. **Нет разрыва в валидации.** Если `GOOGLE_API_KEY` отсутствует, Google SDK сам выдаст ясную ошибку при вызове API. `pydantic-settings` здесь не закрывает реальный баг — он просто сдвигает момент ошибки с runtime на import.
  4. **Принцип прототипа.** AGENTS.md: «No abstractions for single-use code». `pydantic-settings` — абстракция над `os.getenv`, которая окупается при сложном конфиге. Этот конфиг не сложный.
  
  Для справки: шаблон `pyproject.toml` от того же ревьюера содержал `google-genai>=0.1.0` — неверная версия SDK. Напоминание, что внешние советы нужно фильтровать.

---

## Resolution (initial)

Проект инициализирован на VPS (`/home/fixedius/projects/research-pipeline`).

**Выполнено:**
- Структура: `src/`, `tasks/`, `reports/`, `tickets/`, `docs/research/`
- `uv init --name research-pipeline --python 3.12`
- Зависимость: `google-genai==2.11.0`
- `.env.example` — содержит `GOOGLE_API_KEY=your_key_here`
- `README.md` — описание, установка (`uv sync`), запуск (`uv run python src/dispatcher.py`)
- `uv run python -c "import google.genai"` — работает

**Примечание:** на Windows `UV_PYTHON` нужно указывать явно из-за конфликта с Hermes-venv; на VPS не требуется.

---

## Resolution (review — 2026-07-15)

### Внешнее ревью #1 (практические нюансы)
Три замечания касаются T4, не T3:
- **`-f/--file` для больших `task.md`** — учтём в `agent_cli.py`
- **`return_exceptions=True` в `asyncio.gather`** — для sequential-прототипа не нужно, но оставим комментарий на будущее
- **Таймаут 120s → запас** — уже есть в `config.py`

Вывод: T3-база собрана правильно, нюансы уходят в T4.

### Внешнее ревью #2 (SOTA-архитектура)
Принято: `src-layout`, модуляризация, CLI entry point, `ruff` + `pytest`.
Отклонено: `pydantic-settings` (оверкилл).

### Применённые изменения
- Структура: `src/research_pipeline/{config,dispatcher}.py` + `clients/{agent_cli,gemma}.py`
- `pyproject.toml`: `[project.scripts]`, `[build-system]`, dev-зависимости
- Dev-инструменты: `ruff` (format + lint), `pytest` (заготовка)
- Точка входа: `uv run dispatcher` (или `python -m research_pipeline`)
- `uv sync` — проходит без ошибок
- `ruff check` — чисто
