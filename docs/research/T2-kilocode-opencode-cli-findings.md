# T2 Findings — Kilocode & Opencode CLI в неинтерактивном режиме

Исследование проведено 2026-07-15.
**Исправлено 2026-07-15:** пересмотр после внешнего ревью — `--format json` как основной подход.

## Версии

| CLI | Версия | Путь |
|-----|--------|------|
| Kilocode | 7.3.1 | `/usr/bin/kilo` |
| Opencode | 1.17.11 | `/usr/bin/opencode` |

---

## Ключевой вывод: `--format json` решает проблему TTY

**Проблема:** `kilo run` и `opencode run` зависают в `subprocess.run()` без TTY — TUI-библиотеки (Ink, Bubbletea) блокируются на буферизации.

**Решение:** флаг `--format json` переключает CLI в **headless-режим** — TUI не рендерится, вывод идёт как чистый NDJSON-стрим в `stdout`. TTY **не нужен**. `subprocess.PIPE` работает напрямую, без `script` и `pty`.

### Проверено (2026-07-15)

```bash
# Opencode — работает без TTY
echo '' | opencode run --dangerously-skip-permissions --format json 'say hello'
# → NDJSON-стрим: step_start, text, step_finish

# Kilocode — работает без TTY
echo '' | kilo run --auto --format json 'say hello'
# → NDJSON-стрим: step_start, text, step_finish
```

### Структура NDJSON (реальная)

Каждая строка — JSON-объект. Ключевые поля:

```json
{"type":"step_start", "timestamp":..., "sessionID":"ses_...", "part":{...}}
{"type":"text", "timestamp":..., "sessionID":"ses_...", "part":{"type":"text", "text":"hello", "time":{...}}}
{"type":"step_finish", "timestamp":..., "sessionID":"ses_...", "part":{"type":"step-finish", "reason":"stop", "tokens":{"total":19677,"input":19646,"output":11,"reasoning":20,"cache":{"write":0,"read":0}}, "cost":0}}
```

- **Текст ответа:** `event["part"]["text"]` при `event["type"] == "text"`
- **Токены:** `event["part"]["tokens"]` при `event["type"] == "step_finish"`
- **Статус:** `event["part"]["reason"]` — `"stop"` (успех) или `"error"`

---

## Подходы к интеграции: три уровня

### Уровень 1: `--format json` + `subprocess.Popen` (рекомендуемый для Dispatcher PoC)

```python
import subprocess
import json

def run_cli_json(cli: str, prompt: str, timeout: int = 120) -> dict:
    """
    cli: 'kilo' или 'opencode'
    Возвращает: {"text": str, "tokens": dict | None, "exit_code": int, "stderr": str | None}
    """
    noninteractive = '--auto' if cli == 'kilo' else '--dangerously-skip-permissions'
    cmd = [cli, 'run', noninteractive, '--format', 'json', prompt]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    full_text = []
    tokens = None

    try:
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "text":
                    full_text.append(event["part"]["text"])
                elif event.get("type") == "step_finish":
                    tokens = event["part"].get("tokens")
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return {"text": "", "tokens": None, "exit_code": -1, "stderr": "timeout"}
    finally:
        # Читаем stderr ДО wait(), чтобы избежать deadlock при заполнении буфера
        stderr_output = process.stderr.read() if process.returncode is None else None
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    return {
        "text": "".join(full_text),
        "tokens": tokens,
        "exit_code": process.returncode,
        "stderr": stderr_output if process.returncode != 0 else None
    }
```

**Плюсы:**
- TTY не нужен — никаких `script`, `pty`, ANSI-чистки
- Структурированный вывод: текст, токены, статус
- Корректная обработка ошибок (stderr доступен)

### Уровень 2: `serve` + HTTP (Production)

Оба CLI имеют встроенный headless-сервер:

```bash
opencode serve --port 4096 --hostname 127.0.0.1
kilo serve --port 4097 --hostname 127.0.0.1
```

> **⚠️ Не верифицировано:** эндпоинт `/api/session/run` — спекулятивный. При переходе на Level 2 необходимо изучить документацию API обоих CLI или снять трафик с работающего `serve`.

Dispatcher общается по HTTP вместо spawn'а процессов:

```python
import httpx

async def run_via_serve(prompt: str, port: int = 4096):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://127.0.0.1:{port}/api/session/run",  # требует верификации
            json={"prompt": prompt, "auto_approve": True},
            timeout=300.0
        )
        return response.json()["result_text"]
```

**Плюсы:**
- Zero TTY-проблем (чистый HTTP)
- Минимальные накладные расходы (нет spawn'а процессов)
- Мониторинг статуса в реальном времени
- Подходит для автозапуска (systemd/supervisor)

### Уровень 3: Direct API Proxy (если CLI как агент не нужен)

Если задача — чистый анализ текста (без записи файлов и bash), можно вызывать модели напрямую через прокси-эндпоинты `zenmux`/`kilo-proxy` через OpenAI-совместимый SDK, минуя CLI.

**Для Dispatcher'а неактуально** — задача требует именно запуска агентов Kilocode/Opencode с их инструментами (чтение файлов, код).

---

## Уровень 0: `script`/`pty` — DEPRECATED

Предыдущий подход (заворачивание в `script -q -c` или `pty.spawn()`) — **рабочий PoC-хак, но не для архитектуры**.

**Минусы:**
- Ненадёжный парсинг ANSI-кодов
- Потеря телеметрии (токены, tool calls)
- Усложнённое управление процессами (зомби, SIGTERM)
- Ломается при смене форматирования CLI

**Использовать только если `--format json` по какой-то причине недоступен.**

---

## Opencode 1.17.11

### Модели

Прокси-провайдер: **zenmux**. API-ключи не нужны.

Дефолтная модель: `opencode/hy3-free`

Gemma 4 31B **недоступна** через opencode. Только Google AI Studio API (см. T1).

### Флаги `run`

| Флаг | Назначение |
|------|-----------|
| `--dangerously-skip-permissions` | Авто-одобрение пермишенов |
| `--format json` | **Headless-режим, NDJSON** |
| `-m, --model <model>` | Модель |
| `--print-logs` | Логи в stderr |
| `--log-level DEBUG` | Детальные логи |
| `-f, --file <path>` | Прикрепить файл |

### Характеристики

- Exit code: 0 = успех
- Время: ~10с (простой запрос)
- `--format json`: NDJSON в stdout, stderr пуст

### Передача длинных промптов

- Аргументы командной строки: лимит `ARG_MAX` (~2MB на Linux). Для типичных `task.md` достаточно.
- Если промпт может быть длинным — использовать `-f, --file`:
  ```bash
  opencode run --dangerously-skip-permissions --format json -f /tmp/prompt.txt
  ```
- Или `--command` + stdin (heredoc).

---

## Kilocode 7.3.1

### Модели

Прокси-провайдер: **kilo-proxy**. 0 credentials.

Дефолтная модель: `kilo-auto/free`

Gemma 4 31B **недоступна** через kilo. Только Google AI Studio API (см. T1).

### Флаги `run`

| Флаг | Назначение |
|------|-----------|
| `--auto` | Авто-одобрение пермишенов |
| `--format json` | **Headless-режим, NDJSON** |
| `-m, --model <model>` | Модель |
| `--print-logs` | Логи в stderr |
| `--log-level DEBUG` | Детальные логи |
| `-f, --file <path>` | Прикрепить файл |
| `--thinking` | Thinking blocks |

### Характеристики

- Exit code: 0 = успех
- Время: ~7с (простой запрос)
- `--format json`: NDJSON в stdout, stderr пуст

### Передача длинных промптов

- Аргументы командной строки: лимит `ARG_MAX` (~2MB на Linux). Для типичных `task.md` достаточно.
- Если промпт может быть длинным — использовать `-f, --file`:
  ```bash
  kilo run --auto --format json -f /tmp/prompt.txt
  ```

---

## Итоговая таблица

| Параметр | Opencode | Kilocode |
|----------|----------|----------|
| Версия | 1.17.11 | 7.3.1 |
| **Основной подход** | `--format json` | `--format json` |
| TTY нужен? | ❌ Нет (с `--format json`) | ❌ Нет (с `--format json`) |
| Deprecated подход | `script -q -c` | `script -q -c` |
| Production подход | `opencode serve` | `kilo serve` |
| Дефолтная модель | `opencode/hy3-free` | `kilo-auto/free` |
| API ключи | Не нужны (zenmux) | Не нужны (kilo proxy) |
| JSON-формат | NDJSON, `part.text` + `part.tokens` | NDJSON, `part.text` + `part.tokens` |
| Exit code | 0 = успех | 0 = успех |
| Gemma 4 31B | ❌ | ❌ |
