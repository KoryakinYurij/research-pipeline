# Пробный прогон DeerFlow (build-vs-buy эксперимент)

> Цель: за один вечер выяснить, даёт ли готовый ресёрч-агент результат лучше,
> чем наш `dispatcher.py`. Не мигрировать. Просто **измерить**.

## Что нужно (всё уже есть)

| Нужно | Статус |
|---|---|
| VPS с Docker | ✅ есть |
| Ключ MiniMax M3 | ✅ есть |
| Веб-поиск | ✅ DuckDuckGo, **ключ не нужен** (дефолт в `config.example.yaml:659`) |
| Gemma / Kilo / OpenCode | ❌ **не участвуют** |

Проверено чтением исходников `bytedance/deer-flow` (MIT, 78k звёзд, push 2026-07-28).

---

## Шаг 1. Скачать (2 мин)

```bash
cd ~
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
```

## Шаг 2. Создать конфиг (1 мин)

```bash
make config
```

Создаст `config.yaml` из примера.

## Шаг 3. Вписать ключ MiniMax (2 мин)

```bash
cp .env.example .env
nano .env
```

Найти строку и раскомментировать, подставив свой ключ:

```
MINIMAX_API_KEY=твой-настоящий-ключ
```

## Шаг 4. Включить модель в config.yaml (3 мин)

Открыть `config.yaml`, найти секцию `models:` (~строка 417) и
**снять `#`** с блока MiniMax. Должно получиться так:

```yaml
models:
  - name: minimax-m3
    display_name: MiniMax M3
    use: deerflow.models.patched_minimax:PatchedChatMiniMax
    model: MiniMax-M3
    api_key: $MINIMAX_API_KEY
    base_url: https://api.minimax.io/v1
    temperature: 1.0
```

> ⚠️ Отступы в YAML критичны. `- name:` идёт с двумя пробелами.
> `PatchedChatMiniMax` — адаптер DeerFlow под MiniMax, не менять.

Поиск трогать **не надо** — DuckDuckGo уже включён.

## Шаг 5. Запустить (5-15 мин на сборку)

```bash
make docker-init
make docker-start
```

Открыть в браузере: **http://localhost:2026**
(если VPS удалённая — `ssh -L 2026:localhost:2026 user@vps`)

## Шаг 6. Замер

Задать тот же вопрос, что лежит в нашем `tasks/task.md`.

---

## Чек-лист сравнения (заполнить руками)

| Критерий | наш dispatcher | DeerFlow |
|---|---|---|
| Время прогона | | |
| Кол-во источников | | |
| Ссылки реальные (открыл 3 шт.) | | |
| Отвечает на вопрос или «вода» | | |
| Нашёл то, чего я не знал | | |
| Стоимость (токены MiniMax) | | |

**Вывод (заполнить после прогона):**

- [ ] DeerFlow заметно лучше → взять ядром, свои силы вложить в автономность/дисциплину прогонов
- [ ] Примерно одинаково → остаться на своём, он проще и понятнее
- [ ] Наш лучше в: ______________ → строить вокруг именно этого

---

## Если что-то сломалось

| Симптом | Причина / что делать |
|---|---|
| `make: command not found` | `sudo apt install make` |
| Docker не найден | Установить Docker + плагин compose |
| Порт 2026 занят | Посмотреть `docker ps`, освободить |
| Модель не отвечает | Проверить отступы YAML и что ключ в `.env` без кавычек |
| Пустые результаты поиска | DuckDuckGo мог зарейтлимитить — подождать, потом повторить |

Ошибку целиком копировать в чат — разберём.

---

## Альтернатива, если DeerFlow окажется тяжёлым

**Local Deep Research** (MIT, 8.8k, push 2026-07-28) — легче ставится:

```bash
curl -O https://raw.githubusercontent.com/LearningCircuit/local-deep-research/main/docker-compose.yml
docker compose up -d
# http://localhost:5000
```

Умеет бесплатные источники без ключей (arXiv, PubMed, Semantic Scholar).

---

## Контекст решения

- Kilo CLI построен на форке OpenCode (`packages/opencode/` в их репо =
  "Fork of upstream OpenCode"). Значит **dual-CLI не даёт разнообразия движка** —
  различаются только модели. Это подрывает идею cross-summary "общее/различия".
- SOTA на DeepResearch Bench I+II — NVIDIA AI-Q (55.95 / 54.50), архитектура
  planner → researcher → orchestrator + **refiner**. Наличие refiner'а
  подтверждает: Verifier (Phase 2) — концептуально верная идея.
- Ссылки: https://agentresearchlab.com/benchmarks/deepresearch-bench-ii/index.html
