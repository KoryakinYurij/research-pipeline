# T2 — Research: Kilocode & Opencode в неинтерактивном режиме

> **Labels:** `wayfinder:research` `afk`  
> **Status:** ✅ resolved

## Resolution (2026-07-15, revised 2026-07-15)

### Основной подход: `--format json` (headless-режим)

**Флаг `--format json` переключает CLI в headless-режим — TTY не нужен, TUI не рендерится.** Вывод идёт как чистый NDJSON-стрим в `stdout`. `subprocess.PIPE` работает напрямую.

### Opencode 1.17.11
- Команда: `opencode run --dangerously-skip-permissions --format json "prompt"`
- Дефолтная модель: `opencode/hy3-free` (zenmux-прокси, ключи не нужны)
- Вывод: NDJSON-стрим, текст в `event["part"]["text"]`, токены в `event["part"]["tokens"]`
- Exit 0, ~10с

### Kilocode 7.3.1
- Команда: `kilo run --auto --format json "prompt"`
- Дефолтная модель: `kilo-auto/free` (kilo-прокси, 0 credentials)
- Вывод: NDJSON-стрим, идентичная структура
- Exit 0, ~7с

### Production-путь: `serve`
- `opencode serve --port 4096` и `kilo serve --port 4097` — headless HTTP-серверы
- Dispatcher общается через `httpx` (REST/SSE), без spawn'а процессов

### DEPRECATED: `script`/`pty`
Ранее рекомендованный подход (`script -q -c`, `pty.spawn()`) — рабочий PoC-хак, но **не для архитектуры**: ненадёжный парсинг ANSI, потеря телеметрии, зомби-процессы. Использовать только если `--format json` недоступен.

### Gemma 4 31B
Недоступна ни в одном CLI. Только через Google AI Studio API (см. T1).

Подробные примеры кода — в [findings](docs/research/T2-kilocode-opencode-cli-findings.md).

---

## Question

Как надёжно запустить `kilo run` и `opencode run` из Python-скрипта и получить текстовый вывод? Нужно выяснить:

1. **Неинтерактивный режим:** Достаточно ли `kilo run "задача"` для headless-запуска, или нужны дополнительные флаги (`--no-tui`, `--cli`)?
2. **Выход и exit code:** Завершается ли процесс сам после ответа? Какой exit code при успехе/ошибке?
3. **Таймауты:** Сколько примерно длится выполнение? Нужно ли ставить таймаут в `subprocess`?
4. **stdout/stderr:** Куда пишется ответ — в stdout или stderr? Есть ли лишний вывод (баннеры, прогресс-бары) который нужно фильтровать?
5. **Передача длинного текста:** Есть ли ограничение на длину аргумента командной строки? Возможно, нужен stdin или временный файл?

**Результат:** Markdown-файл с примерами команд и описанием поведения для каждого CLI.
