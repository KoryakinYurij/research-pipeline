# Аудит research-pipeline: карта Phase 2 и findings

*Независимый аудит · KoryakinYurij/research-pipeline*

## Карта Phase 2 (Verifier) и её research-findings: разбор по фактам

Прочитал MAP.md, MAP-phase2.md, HANDOFF.md и все findings в `docs/research/`, сверил семь первоисточников (Anthropic, OpenAI, STORM, VeriMAP, Multi-agent Debate, Self-Refine, LLM-as-a-Judge) с оригиналами в вебе и проверил технические факты про Gemma 4, Kilocode/Opencode CLI и Hermes + MiniMax M3. Ниже — что подтвердилось, что дыра, и на что опираться можно, а что нет.

[Открыть репозиторий ↗](https://github.com/KoryakinYurij/research-pipeline) · [Короткий вывод](#verdict)

**Навигация:** [Вывод](#verdict) · [Проект](#overview) · [Источники](#sources) · [Дыры](#gaps) · [Надёжность](#reliability) · [SOTA](#sota) · [Рекомендации](#recommendations)

---

## Коротко

Findings — необычно дисциплинированные для авто-исследования. Опираться на них можно — но только на то, что промаркировано как факт, а не на раздел «предложение» в конце.

| Поле | Значение |
|---|---|
| **Phase 1 — Dispatcher** | Готово и e2e-подтверждено |
| | Smoke-тест «pong» прогнан реально (2026-07-16, 2026-07-22 с Gemma). Код, а не только план — можно опираться. |
| **Качество research-findings** | Высокое, с оговорками |
| | 7/7 проверенных первоисточников — реальны и переданы точно. Авторы сами вскрыли и исправили галлюцинации прошлой версии. |
| **Готовность плана Phase 2** | Спецификация, не билд |
| | Ключевой компонент (Hermes-судья) не тестировался технически. Пороги вердикта — «TBD». |
| **Найдено дыр** | 2 критичные · 2 высоких · 4 средних · 2 низких |
| | Подробности ниже — от несанкционированного судьи до отсутствия песочницы. |

---

## Что это за проект

Прототип на Python/uv: `task.md` отправляется двум независимым CLI-агентам (Kilocode и Opencode), их сырые ответы объединяются в отчёт, а Gemma 4 31B делает кросс-саммари. Phase 1 (Dispatcher) полностью реализован и верифицирован. Phase 2 (Verifier) — только карта (`MAP-phase2.md`) плюс объёмное research-findings по литературе, реализация ещё не начата.

**Пайплайн:**

| Шаг | Описание |
|---|---|
| `task.md` | Текстовая задача (формат намеренно не зафиксирован) |
| Kilocode CLI | headless run --auto --format json (NDJSON) |
| Opencode CLI | headless run --dangerously-skip-permissions --format json |
| Gemma 4 31B | кросс-саммари: общее / различия / на что смотреть |
| `report.md` | Phase 1 destination — уже достигнуто |
| Verifier (Phase 2, план) | Layer A (код-гейты) + Layer B (LLM-rubric) + ≤1 follow-up |

---

## Проверка источников

Каждый первоисточник из `docs/research/verifier-phase2-findings.md` и обоих T1/T2-findings я перепроверил в вебе отдельно от репозитория — по официальной документации, arXiv-страницам и независимым обзорам.

### Подтверждено

**Anthropic — Evaluator-Optimizer workflow ("Building effective agents", 19 Dec 2024)**
*Источник: `docs/research/verifier-phase2-findings.md §1.1`*
Пост существует, содержание передано точно: генератор + оценщик, критерии + stop-condition, никакого фиксированного N=1. Авторы репозитория сами отметили, что предыдущий черновик выдумал «N=1 обязателен» — в текущей версии это исправлено.

**OpenAI Deep Research — 3-шаговый product path (clarify → rewrite → research)**
*Источник: `docs/research/verifier-phase2-findings.md §1.2`*
Соответствует официальной документации и лончу (Feb 2025). Важный, часто упускаемый нюанс подсвечен верно: в API нет автоматического clarify/rewrite — это забота разработчика.

**Stanford STORM = Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking**
*Источник: `docs/research/verifier-phase2-findings.md §1.3`*
arXiv:2402.14207 подтверждает и расшифровку акронима, и то, что это pre-writing/outline система, а не verification loop — в первом (забракованном) драфте это было перепутано.

**VeriMAP — Planner/Executor/Verifier/Coordinator, Python+NL Verification Functions, retries=3 / replans=5**
*Источник: `docs/research/verifier-phase2-findings.md §1.4`*
Проверено напрямую по arXiv:2510.17109 (Oct 2025). Архитектура и цифры совпадают. Ключевой вывод сформулирован честно: «cross-model auditing» — это НЕ то, что делает VeriMAP; портируется только идея acceptance-criteria на подзадачу.

**Self-Refine + LLM-as-a-Judge (Zheng et al., MT-Bench) — биасы judge'а: позиция, многословность, self-enhancement**
*Источник: `docs/research/verifier-phase2-findings.md §1.6–1.7`*
Обе статьи существуют (arXiv:2303.17651, arXiv:2306.05685), выводы про биасы переданы корректно и прямо превращены в требование к промпту судьи (анти-порядок, анти-многословность).

**Gemma 4 31B, Apache 2.0, 256K контекст, доступна через Google AI Studio (T1 findings)**
*Источник: `docs/research/T1-google-ai-studio-sdk-findings.md`*
Звучало как галлюцинация (номер версии, «31B» не из типичной линейки Gemma) — но веб-поиск подтвердил релиз 2 апреля 2026: линейка E2B/E4B/26B-MoE/31B-Dense, Apache 2.0, 256K контекст. Находка технически точная.

**Kilocode/Opencode CLI: --format json = headless NDJSON, TTY не нужен, текст в part.text**
*Источник: `docs/research/T2-kilocode-opencode-cli-findings.md`*
Подтверждено независимой документацией CLI (opencode.ai/docs, kilo.ai/docs) и код-примерами сообщества — структура события и флаги совпадают до буквы.

### С нюансом

**Multi-agent Debate (Du et al.) + оговорки поздних работ (сycophancy, over-deliberation)**
*Источник: `docs/research/verifier-phase2-findings.md §1.5`*
Базовая статья (arXiv:2305.14325) передана верно. Авторы сами честно пометили оговорки как «не проверено по первоисточникам» — это плюс к дисциплине, но также значит: эту часть нельзя цитировать как «доказано».

### Пробел

**Hermes + MiniMax M3 как судья Layer B — «headless-путь ещё не изучен» (P2-T2 открыт)**
*Источник: `MAP-phase2.md`, Not yet specified*
MiniMax M3 и Hermes Agent реальны (релиз M3 — июнь 2026, open-source агент Nous Research), но это **не бесплатные CLI-прокси**, как Kilo/Opencode — это платный API. Именно тот класс риска, который T2 закрыл для Kilo/Opencode (TTY, тайминги, id модели), для Hermes ещё не закрыт вообще.

---

## Дыры в плане (MAP-phase2.md)

10 находок, отсортированных по серьёзности. Часть из них авторы уже сами честно пометили как «Not yet specified» — это хорошо (осознанный долг), но это всё ещё риск, если план начнут реализовывать «как есть».

### Критично

**Судья Layer B (Hermes + MiniMax) технически не исследован**
Вся архитектура Verifier построена вокруг «Hermes + Minimax M3 only», но headless-режим Hermes ещё не проверен на этом VPS (P2-T2 — открытый тикет). До T2 Kilocode/Opencode тоже «зависали без TTY» — ровно тот же класс сюрпризов может ждать и здесь. Строить Phase 2 map вокруг неподтверждённого компонента — риск переписывать архитектуру на полпути.
*Источник: `MAP-phase2.md → Not yet specified; HANDOFF.md`*

**Автономное выполнение кода без песочницы, теперь ещё и в цикле**
Kilo/Opencode запускаются с --auto / --dangerously-skip-permissions — полный автономный доступ к файловой системе и shell на VPS. Пока это ручной запуск — риск управляем. Но Verifier добавляет автоматический follow-up: NEEDS_WORK → сам перезапускает оба CLI на gap-task без человека в цикле. Blast radius растёт, а про изоляцию (контейнер/firejail/read-only fs) в карте нет ни слова.
*Источник: `T2 findings; MAP-phase2.md Decisions «Follow-up policy»`*

### Высокая

**Смена стоимостной модели: бесплатные CLI → платный API-судья**
Phase 1 сознательно построен на free-tier прокси (kilo-auto/free, deepseek-v4-flash-free, Gemma free tier). Phase 2 вводит MiniMax M3 через Hermes — это платный API ($0.3–0.6/M input). В карте нет ни бюджетного потолка, ни оценки стоимости одного verdict-цикла (Layer B + возможный follow-up = 3-и раза больше токенов).
*Источник: `verifier-phase2-findings.md §4.4; внешний прайсинг MiniMax M3`*

**Ретраи и degraded mode официально «не специфицированы»**
Если один CLI падает, а второй отвечает — пайплайн это переживёт (soft-fail на FileNotFoundError есть), но нет решения, что считать финальным отчётом в таком случае и нужно ли ретраить. Авторы сами держат это в разделе «Not yet specified» — то есть решение осознанно отложено, но это прямая дыра перед автоматизацией watch-режима.
*Источник: `MAP.md → Not yet specified`*

### Средняя

**Пороговые значения Layer B и политика строгости — TBD**
Destination Phase 2 сформулирован как «shipped & eval'd», но какие измерения обязательны, какие cutoff-баллы, и что хуже — false APPROVED или false NEEDS_WORK — всё «TBD in grilling». Пока это не зафиксировано, «MVP Verifier» рискует превратиться в бесконечный продуктовый спор внутри тикета P2-T1.
*Источник: `MAP-phase2.md Decisions/Not yet specified; findings §4.2`*

**Дрейф free-моделей провайдеров (zenmux / kilo-proxy) не отслеживается**
kilo/kilo-auto/free и opencode/deepseek-v4-flash-free — алиасы бесплатных моделей у прокси-провайдеров. Такие алиасы меняют «начинку» без предупреждения. В T4 уже была одна поломка на регистре имени модели (gemma-4-31B-it → gemma-4-31b-it). Нет контрактного smoke-теста, который бы ловил такой дрейф автоматически.
*Источник: `HANDOFF.md (Gemma casing bug); T2 findings`*

**Формат task.md не зафиксирован, а Layer B уже на него опирается**
Rubric «task_coverage» из findings §4.2 явно требует явных пунктов/вопросов в task.md. Но формат task.md намеренно оставлен «просто текстом» до появления Composer'а. Если Composer придёт с другой структурой, часть рубрики Layer B придётся переписывать.
*Источник: `MAP.md → Not yet specified «Формат task.md»`*

**Не рассмотрены готовые LLM-eval фреймворки как альтернатива самописному Layer B**
Ни один из 7 первоисточников исследования не сравнивается с готовыми инструментами оценки (DeepEval/G-Eval, RAGAS, Arize Phoenix, LangSmith/OpenEvals, OpenAI Evals) — а они как раз закрывают «структурированный JSON-вердикт + rubric + anti-bias» из коробки, без необходимости поднимать headless Hermes.
*Источник: Пробел в `docs/research/verifier-phase2-findings.md` — подтверждено отдельным веб-исследованием*

### Низкая

**Последовательные (не параллельные) вызовы CLI — осознанный, но не пересмотренный trade-off**
agent_cli.py уже async, dispatcher.py вызывает Kilo и Opencode строго по очереди «для простоты». Follow-up удваивает это. asyncio.gather() дал бы 2x снижение latency почти бесплатно — не исследование, а 10-минутный рефактор.
*Источник: `dispatcher.py; MAP-phase2.md Notes «CLI order today: sequentially»`*

**Тестовое покрытие — только парсинг NDJSON**
11 unit-тестов покрывают только _parse_ndjson_text. Нет тестов на dispatcher.run_pipeline, на ошибки Gemma-клиента, нет CI (ruff/pytest гоняются вручную). Для прототипа нормально, но перед Phase 2 automation (watch-режим) это стоит закрыть.
*Источник: `HANDOFF.md «P1 Hygiene fixes»`*

---

## Можно ли опираться на findings?

Ответ разный для разных слоёв документа — литературный обзор, инженерное предложение и нереализованные предположения нужно оценивать по-разному.

**Да — по фактам из литературы**
Все 7 первоисточников реальны, процитированы с URL/arXiv ID и переданы без искажений. Более того: авторы явно зафиксировали раздел «Мифы закрыты», где сами вскрыли и удалили выдуманные вещи из предыдущего черновика («Delta-Tasking» как SOTA-паттерн, «экономия 70% токенов», неверная расшифровка STORM, ложная привязка VeriMAP к cross-model-аудиту). Это редкий и сильный сигнал — большинство AI-исследований такую самокритику не проходят.

**Осторожно — с разделом «предложение» (§4 findings)**
Дизайн Verifier'а (Layer A/B, follow-up-политика, judge = Hermes/Minimax) сами авторы называют «design implications, not SOTA» — то есть инженерным выводом из литературы, а не тем, что где-то доказано. Это нормально и честно, но значит: нельзя защищать конкретные пороги («false NEEDS_WORK лучше false APPROVED», «follow-up ровно 1 раз») ссылкой на исследование — это продуктовое решение, которое ещё не прошло через собственный eval-план авторов (§4.6).

**Нет — по компонентам, которые ещё не тронуты руками**
Судья Hermes+MiniMax M3 и весь Layer B построены на предположении, что headless-режим Hermes будет вести себя предсказуемо. До того как это будет исследовано так же, как T2 исследовал Kilocode/Opencode (реальные флаги, TTY-поведение, лимиты, id моделей), любые конкретные тайминги/промпты для Verifier — гипотеза, а не факт.

---

## Что упущено: готовый SOTA-ландшафт LLM-eval инструментов (2026)

Findings честно разбирают академическую литературу (Anthropic, VeriMAP, STORM и т.д.), но ни разу не сравниваются с уже существующими production-фреймворками для оценки LLM/агентов. А ведь именно они закрывают ровно то, что нужно для Layer B — структурированный вердикт + rubric + защита от биасов judge'а — без необходимости поднимать headless Hermes с нуля.

| Инструмент | Сильная сторона | Как применимо здесь |
|---|---|---|
| DeepEval (G-Eval, DAG-метрики) | pytest-нативный, кастомные LLM-judge критерии, JSON/tool-correctness метрики | Может закрыть весь Layer B прямо сейчас: G-Eval позволяет описать rubric (task_coverage, evidence_quality) в 15–20 строк без разработки headless-интеграции с Hermes. |
| RAGAS | faithfulness / context precision-recall, если появится источник-based research (RAG) | Пригодится, если Composer начнёт давать агентам внешние источники для ресёрча — сейчас не критично, но стоит держать в уме на будущее. |
| Arize Phoenix | трассировка агентных траекторий, self-hosted, OTel-нативный | Полезен, когда появится watch-режим / автоматизация — даст наблюдаемость над обоими CLI-прогонами без самописного логирования. |
| OpenAI Evals | YAML model-graded eval, воспроизводимые бенчмарки | Хороший формат именно для eval-плана из §4.6 findings (5–10 задач, human-labels vs verdict) — не придётся изобретать свой ранлоадер экспериментов. |
| LangSmith / OpenEvals | trajectory-match режимы, если пайплайн когда-нибудь перейдёт на LangGraph | Не приоритет сейчас (проект сознательно избегает лишних абстракций), но полезная точка сравнения при решении «строить свой Verifier или взять готовый харнесс». |

Не значит «отменить Hermes/Minimax» — проект осознанно избегает лишних абстракций (см. отказ от pydantic-settings в T3). Но перед тем как писать headless-интеграцию с Hermes с нуля, стоит хотя бы 30 минут сравнить её с готовым G-Eval-метриком — это дешёвая проверка гипотезы «нужен ли вообще кастомный судья».

---

## Что сделать по-другому

Не «переделать всё», а точечно закрыть риски до того, как Phase 2 перейдёт из карты в код.

**01 · Сначала de-risk судью, потом — архитектуру**
Прежде чем фиксировать Verifier map, сделать P2-T2 (Hermes headless research) в стиле T2: реальные флаги, поведение без TTY, лимиты, id модели. Если Hermes окажется проблемным — дешевле узнать это до, а не после написания Layer B кода.

**02 · Сравнить с G-Eval/DeepEval, прежде чем писать rubric с нуля**
Потратить один спайк на то, чтобы описать Layer B через готовую LLM-judge библиотеку. Если она закрывает 80% потребности за 20 строк — не изобретать колесо, оставить кастом только там, где нужна интеграция с task.md/gap-task.

**03 · Зафиксировать пороги ДО кода**
false APPROVED vs false NEEDS_WORK, cutoff-баллы, обязательные измерения — провести grilling-сессию (P2-T1) и записать решения в MAP как «Decisions», а не оставлять «TBD» на этапе имплементации.

**04 · Добавить бюджетный потолок на Verifier-цикл**
MiniMax M3 — платный API. Посчитать стоимость одного verdict + возможного follow-up (Layer B call + 2 CLI-рана) и жёстко ограничить это в конфиге, аналогично CLI_TIMEOUT.

**05 · Изоляция перед автоматическим follow-up**
Пока follow-up запускается вручную — риск приемлем. Перед автоматизацией (watch-режим) — обернуть CLI-запуски в контейнер/ограниченного пользователя, раз агенты получают auto-approve на файловые и shell-операции.

**06 · Контрактный smoke-тест на модели-алиасы**
Лёгкий периодический прогон smoke.md, который алертит при смене поведения/имени free-моделей у zenmux/kilo-proxy — тот же класс бага, что уже был с регистром gemma-4-31b-it, но обнаруженный автоматически, а не вручную.

**07 · Распараллелить Kilo/Opencode уже сейчас**
asyncio.gather(run_kilocode(...), run_opencode(...)) — быстрый выигрыш по latency без всякого исследования, независимо от Phase 2.

**08 · Явно решить degraded-mode**
Зафиксировать: если один CLI упал — отчёт помечается как «partial», Verifier обязан это увидеть на уровне Layer A (уже почти есть в рубрике «at least one agent succeeded») и не пытаться судить как полноценный.

---

## Источники, использованные для перепроверки

- [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [OpenAI — Deep research API guide](https://developers.openai.com/api/docs/guides/deep-research)
- [Shao et al. — STORM, arXiv:2402.14207](https://arxiv.org/abs/2402.14207)
- [Xu et al. — VeriMAP, arXiv:2510.17109](https://arxiv.org/abs/2510.17109)
- [Du et al. — Multiagent Debate, arXiv:2305.14325](https://arxiv.org/abs/2305.14325)
- [Madaan et al. — Self-Refine, arXiv:2303.17651](https://arxiv.org/abs/2303.17651)
- [Zheng et al. — LLM-as-a-Judge, arXiv:2306.05685](https://arxiv.org/abs/2306.05685)
- [Gemma releases — ai.google.dev](https://ai.google.dev/gemma/docs/releases)
- [Kilo CLI reference](https://kilo.ai/docs/code-with-ai/platforms/cli-reference)
- [OpenCode CLI guide](https://open-code.ai/en/docs/cli)

---

Аудит подготовлен на основе публичного состояния репозитория [KoryakinYurij/research-pipeline](https://github.com/KoryakinYurij/research-pipeline) (ветка master). Не аффилирован с автором репозитория.
