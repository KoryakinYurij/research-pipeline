# HANDOFF — T4 Dispatcher Prototype (2026-07-16)

## Что сделано в этой сессии

Дописан и отлажен `agent_cli.py` — модуль для вызова Kilocode и Opencode в headless-режиме из Python (asyncio).
Дописан `dispatcher.py` — добавлен `flush=True` на все print'ы (иначе вывод теряется без TTY).

## Текущий статус

- ✅ `agent_cli.py` — **работает**. Тест `run_kilocode("2+2?")` возвращает `{'text': '4', ...}`.
- ✅ `dispatcher.py` — код корректен, ruff чисто.
- ❌ Полный прогон пайплайна (`uv run python src/research_pipeline/dispatcher.py`) — **не удалось проверить** из-за проблем с basher-агентом (путает команды, не захватывает вывод).

## Ключевые архитектурные решения (финал)

### agent_cli.py

```python
# Прямой вызов CLI через asyncio.create_subprocess_exec (без shell!)
# stdin=DEVNULL — КРИТИЧНО: оба CLI виснут без этого
# NDJSON-структура: {"type":"text", "part":{"text":"..."}}
#   └─ текст в part.text, а НЕ в корне obj.text!
# Модели: kilo/kilo-auto/free и opencode/deepseek-v4-flash-free
# stderr читается конкурентно (asyncio.create_task) — иначе deadlock
# Общий таймаут через asyncio.timeout()
```

### dispatcher.py

```python
# Все print() с flush=True — без этого вывод буферизируется и теряется при timeout
# Последовательное выполнение: kilo → opencode → gemma cross-summary
```

## Проверенные факты

### Что работает (протестировано в этой сессии)

```bash
# Оба CLI работают с --format json при < /dev/null (stdin=DEVNULL в коде)
echo '' | timeout 30 kilo run --auto --format json "2+2?" < /dev/null
# → {"type":"text","part":{"text":"4",...}}

echo '' | timeout 30 opencode run --dangerously-skip-permissions --format json "2+2?" < /dev/null
# → {"type":"text","part":{"text":"4",...}}

# С явным указанием free-моделей — тоже работает
kilo run --auto --format json --model kilo/kilo-auto/free "2+2?" < /dev/null
opencode run --dangerously-skip-permissions --format json -m opencode/deepseek-v4-flash-free "2+2?" < /dev/null
```

### Модели

| CLI | Free-модель | Примечание |
|-----|------------|------------|
| Kilocode 7.3.1 | `kilo/kilo-auto/free` | Из конфига `~/.config/kilo/kilo.jsonc` |
| Opencode 1.17.11 | `opencode/deepseek-v4-flash-free` | Из `opencode models`, **не** `deepseek/deepseek-v4-flash-free` |
| Opencode (альт.) | `opencode/hy3-free`, `opencode/mimo-v2.5-free` | Другие free-модели |

### NDJSON-структура (реальная, проверена)

```json
{"type":"step_start","part":{"id":"...","type":"step-start",...}}
{"type":"text","part":{"id":"...","type":"text","text":"4",...}}     ← текст ЗДЕСЬ
{"type":"step_finish","part":{"id":"...","type":"step-finish",...}}
```

**Важно:** текст в `part.text`, а не в корневом `text`! Это отличает от структуры `{"type":"text","text":"..."}` которую предлагают некоторые источники.

### Opencode: флаги

- `--dangerously-skip-permissions` — **правильный** флаг для headless (не `--auto`, его нет в v1.17.11)
- `--format json` — работает, выдаёт NDJSON
- `-m provider/model` — указание модели (не `--model`)

## Нерешённая проблема

**Полный прогон пайплайна не удалось верифицировать.** Basher-агент систематически не захватывал вывод (возможно, из-за буферизации Python stdout или неправильной обработки shell-команд).

### Как проверить пайплайн (следующему агенту)

```bash
# 1. Убить висящие процессы
pkill -9 -f 'kilo run'; pkill -9 -f 'opencode run'

# 2. Проверить импорты и простой вызов
cd /home/fixedius/projects/research-pipeline
uv run python -c "
import asyncio
from research_pipeline.clients.agent_cli import run_kilocode
result = asyncio.run(run_kilocode('What is 2+2?', timeout=30))
print(f'OK={result[\"ok\"]}, text={result[\"text\"]!r}')
"
# Ожидается: OK=True, text='4'

# 3. Запустить полный пайплайн (важно: PYTHONUNBUFFERED=1 + python -u)
PYTHONUNBUFFERED=1 uv run python -u src/research_pipeline/dispatcher.py

# Или через python -m:
PYTHONUNBUFFERED=1 uv run python -u -m research_pipeline
```

### Возможные причины зависания

1. **CLI_TIMEOUT=120** (в config.py) — каждый CLI может висеть до 2 минут. Для task.md длиной 230 байт это многовато. Возможно, CLI долго думают над реальной исследовательской задачей.
2. **API-ключи не настроены** — оба CLI используют free-tier роутинг, но без ключей могут быть задержки.
3. **Вывод буферизируется** — даже с `flush=True` и `PYTHONUNBUFFERED=1`, возможна буферизация на уровне piping в basher-агенте.
4. **Basher-агент глючит** — в этой сессии систематически путал команды (запускал `--help` вместо run, `ls` вместо pipeline).

## Что НЕ делать

- ❌ Не использовать `script -q -c` — проверено, это тупиковый путь (проблемы с shell-экранированием многострочных промптов).
- ❌ Не использовать `--model kilo-auto/free` без префикса `kilo/` — `ProviderModelNotFoundError`.
- ❌ Не использовать `deepseek/deepseek-v4-flash-free` без префикса `opencode/` — `UnknownError`.
- ❌ Не ставить таймауты >60s на тесты — если работает, то быстро.
- ❌ Не передавать prompt через файл (`-f`) — это «прикрепить файл к сообщению», а не «прочитать prompt из файла».

## Файлы, изменённые в этой сессии

- `src/research_pipeline/clients/agent_cli.py` — полностью переписан
- `src/research_pipeline/dispatcher.py` — добавлен `flush=True` во все `print()`
