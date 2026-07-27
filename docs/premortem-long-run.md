# Premortem: research-pipeline (long-run failure)

**Дата написания:** 2026-07-25  
**Горизонт сценарного «сейчас»:** +12–18 месяцев  
**Статус системы в сценарии:** мёртв, заброшен, или активно вредит / недостоверен  
**Объект:** `/home/fixedius/projects/research-pipeline`  
**Метод:** premortem (не статус-репорт, не план «как починить код»)

---

## 0. Ground truth (на момент premortem)

Проверено по репо; это опора для нарративов, не описание желаемого.

### Phase 1 Dispatcher — shipped

```
task.md (freeform text)
  → Kilocode CLI  (sequential, first)
  → Opencode CLI  (sequential, second)
  → raw → reports/kilocode-output.md, reports/opencode-output.md  (overwrite each run)
  → Gemma 4 31B cross-summary (optional; soft-skip / soft-error)
  → reports/report-{timestamp}.md
```

| Компонент | Факт в коде |
|-----------|-------------|
| Стек | Python 3.12 / `uv`, `src/research_pipeline/` |
| Kilo | `kilo run --auto --model kilo/kilo-auto/free --format json` |
| Opencode | `opencode run --dangerously-skip-permissions -m opencode/deepseek-v4-flash-free --format json` |
| Таймаут | `CLI_TIMEOUT` default **120s**; `start_new_session` + `os.killpg` на timeout |
| Soft-fail | `FileNotFoundError` → `ok=False`, pipeline **всё равно пишет report** |
| Парсинг | NDJSON только `type=="text"` → `part.text`; остальное молча drop |
| Gemma | `gemma-4-31b-it` / `GOOGLE_API_KEY`; нет ключа → placeholder markdown |
| Тесты | 11 unit-тестов `_parse_ndjson_text`; **нет** E2E/CI полного pipeline |
| Degraded mode | **не реализован** (MAP.md: «позже»); partial success не блокирует артефакт |
| State / audit | нет `verdict.json`, нет run-id на raw, нет ledger прогонов |

### Phase 2 Verifier — charted, **не shipped**

Карта: `MAP-phase2.md`. Тикеты `P2-T1`…`P2-T6` — open.  
План: Layer A (code) + Layer B (Hermes + **Minimax M3 only**, paid) + max **1** follow-up (оба CLI на gap task, append `## Follow-up`) + `verdict.json`.  
Строгость: prefer false **NEEDS_WORK**. Cost ceiling **required, numbers TBD**. Sandbox **gate** для unattended watch. Free-tier alias drift — post-MVP / fog.

### Скрытые «частичные» защиты уже в map (но не в prod-коде)

- Max 1 follow-up (policy on paper).
- Sandbox before unattended (policy on paper).
- Cost ceiling for Verifier cycle (required, **не численно**).
- Process-group kill + CLI soft-fail (Phase 1 code — только subprocess hygiene).
- Findings: judge ≠ Gemma; bias hygiene; eval corpus before claim «works».

---

## 1. Failure narratives (как будто уже случилось)

### N1 — «Free-tier alias drift: отчёты живые, смысл мёртв»

К весне 2027 free-алиасы `kilo/kilo-auto/free` и `opencode/deepseek-v4-flash-free` несколько раз сменили backend без смены model id. Smoke `tasks/smoke.md` («pong») продолжал зелёным: exit=0, chars>0, Gemma писала «оба агента согласны». На реальных `task.md` оба агента выдавали уверенный, связный, **фактически пустой** web-slop. NDJSON-схема не менялась — unit-тесты парсера оставались green. Через квартал никто не мог сказать, *какой* model family реально писал research; папка `reports/` выглядела как работающая система.

**Механизмы:** hardcoded free aliases в `agent_cli.py`; alias = marketing handle, не pin; smoke не ловит quality; нет contract smoke / snapshot ответов на golden task; map явно отложил «model alias drift» post-MVP.

**Ранние индикаторы (игнорируемые):** расхождение длины/стиля между kilo и opencode без смены кода; «оба согласны» на спорных темах чаще, чем раньше; step_finish cost/tokens (есть в NDJSON, **не сохраняются** в report) скачут; HANDOFF/T2 model table устарела, код не.

**Кто страдает:** operator (ложное чувство «pipeline работает»); будущий агент (нет model provenance в артефакте); consumers отчётов (решения на silent quality collapse).

**Класс:** **Certain / high-probability** при любой эксплуатации >нескольких месяцев без pin/smoke quality.

---

### N2 — «Phase 2 так и не вышел; Phase 1 стал складом недоверия»

Verifier-тикеты годами «open»: P2-T1 (criteria HITL) ждал человека, P2-T2 (Hermes headless) упёрся в auth/flags, eval corpus (P2-T3) так и не собрали. Dispatcher при этом оставался удобным: один вызов — красивый `report-*.md` с тремя секциями. Люди и агенты начали **цитировать** cross-summary Gemma как «синтез двух независимых исследований». Когда первый серьёзный промах всплыл в принятом решении, весь каталог `reports/` пометили «нельзя доверять»; проект не удалили — просто перестали запускать. «Dead by accumulation of untrusted paper.»

**Механизмы:** destination Phase 1 = «работающий прототип», destination Phase 2 = «shipped & eval’d», но **потребление** Phase 1 артефактов не gated; нет watermark «UNVERIFIED»; Gemma prose *выглядит* как verdict; findings сами предупреждают: Verifier worth only if decision+action, иначе essay.

**Ранние индикаторы:** P2-T* месяцами open; reports растут, `verdict.json` = 0; human skim только секции «Что общего»; CONTEXT.md термины Verdict/Layer A существуют, кода нет.

**Кто страдает:** report consumers (главные); operator (репутация/ложный прогресс); future agent (наследует кучу md без machine gate).

**Класс:** **Certain / high-probability**, если Phase 2 остаётся blocked на HITL/research, а Phase 1 уже «полезен».

---

### N3 — «Двойной free-агент: redundancy theater»

На задачах уровня «сравни X и Y / что такое Z» оба free-модели сходились в одних и тех же популярных мифах (общие training priors + один и тот же класс web noise). Gemma cross-summary честно писала: «расхождений нет; оба подчёркивают…» — и это **усиливало** доверие, хотя независимость была иллюзией (два weak generator'а, не adversarial debate). Findings (MAD / Zheng) предупреждали про shared mistakes и sycophancy; в коде нет ни score disagreement, ни требования evidence — только prose.

**Механизмы:** dual-CLI = независимость *инстансов*, не *эпистемики*; free models часто same-tier; sequential prompt identical full `task.md`; no citation/tool-trace retention in final report; agreement treated as signal of truth by readers (and later by a naive Layer B).

**Ранние индикаторы:** high lexical overlap A/B; Gemma «расхождений нет» на задачах, где эксперт ждал разброс; sorting/research удачные только когда агенты писали код на диске (как ручной sorting-comparison), а не pure LLM essay.

**Кто страдает:** consumers; operator, который продавал «два агента = надёжнее».

**Класс:** **Certain / high-probability** на open-ended research без tools/evidence gate; слабее на задачах с executable check.

---

### N4 — «Paid judge + strict NEEDS_WORK: смерть от чека»

Когда Verifier наконец включили, strict defaults (prefer false NEEDS_WORK) + vague `task.md` + free-tier thin reports дали **систематический** NEEDS_WORK. Max 1 follow-up ограничивал depth, но не **volume**: каждый cycle = Layer B (Minimax $) + до 2× CLI wall-time + optional second path. Cost ceiling в map «required» — **числа так и TBD**, в коде cap не оказалось (или cap был «мягкий»). Оператор крутил 20–40 задач/неделя «на автомате» → счёт и latency взорвались; follow-up append добавлял ещё один слой slop без merge. Через два месяца «Verifier» отключили, чтобы «просто гонять dispatcher» — полный круг к N2.

**Механизмы:** paid judge on every run; strictness without task quality bar; max-1 не спасает от N tasks × (1+follow-up); cost ceiling not locked in P2-T1/T2; dual-CLI follow-up always (map decision) doubles burn; false NEEDS_WORK wastes money by design if criteria over-strict on free-tier input.

**Ранние индикаторы:** P2-T6 eval table: high NEEDS_WORK + human «report was fine»; $/report unknown; Hermes latency >> CLI; no budget env var analogous to `CLI_TIMEOUT`.

**Кто страдает:** operator (деньги/время); future agent (follow-up loops в watch); consumers (delayed or abandoned runs).

**Класс:** **Conditional** — если Verifier ship + volume/automation; **high** при unattended/watch без hard $ cap.

---

### N5 — «`--auto` / `--dangerously-skip-permissions` на VPS: security self-own»

Follow-up и затем watch-mode завели **без** sandbox (map gate: «no auto-watch until isolation» — нарушили «на один вечер»). Gap task от Minimax содержал формулировки, которые free-агенты с tools интерпретировали как действия на хосте. Opencode с `--dangerously-skip-permissions` и kilo с `--auto` уже были production path Phase 1. Один «исследовательский» прогон затронул credentials / home / соседние проекты. После инцидента pipeline запретили на машине; проект стал toxic asset.

**Механизмы:** headless flags *by design* strip human confirm; agents are tool-using coding CLIs, not pure chat; gap task = LLM-written, not human-reviewed in auto mode; no container/firejail/restricted user in Phase 1; raw prompt = full task text to subprocess; VPS often multi-purpose.

**Ранние индикаторы:** map fog «CLI isolation design»; any successful tool use outside `reports/`; desire to «just cron it»; secrets in env visible to child processes.

**Кто страдает:** operator (host integrity); future agent (banned tooling); indirectly any consumer of machine.

**Класс:** **Conditional** на automation/follow-up unattended; **Certain** severity *if* that path is taken without isolation. Phase 1 manual single-shot — lower probability, non-zero if task itself asks dangerous work.

---

### N6 — «Judge rubber-stamp / systematic wrong → human перестал читать»

Два исхода одного корня.

**6a Rubber-stamp:** Layer B (или pre-Verifier habit: «Gemma section 3 = достаточно») одобрял длинные, структурно красивые отчёты. Verbosity bias (Zheng et al., findings §1.7) + fixed order Kilocode→Opencode + no position swap. False APPROVED на thin evidence. После 1–2 месяцев human trust → skim title only.

**6b Systematic strict-wrong:** наоборот, judge клеймил NEEDS_WORK за «нет источников» там, где task не требовал, или BLOCKED на нормальных briefs. Human начал **игнорировать verdict** и открывать raw — verdict стал noise.

В обоих случаях машина продолжала писать `verdict.json` / markdown; **доверие** умерло. «Actively untrustworthy»: люди либо слепо верят, либо слепо не верят — одинаково плохо для research pipeline.

**Механизмы:** LLM-as-judge without durable human calibration (P2-T6 never sustained); no gold tasks; criteria TBD then frozen wrong; Gemma summarizer ≠ judge but *looks* authoritative; no audit trail of human overturns.

**Ранние индикаторы:** agreement rate human↔verdict unknown; zero overturn log; APPROVED correlates with length; operator quotes Gemma not sources.

**Кто страдает:** consumers (6a); operator time (6b); future agent (learns wrong prior from verdicts).

**Класс:** **High-probability** for 6a if Phase 2 never ships but Phase 1 is trusted; **Conditional** for formal verdict after weak P2-T6.

---

### N7 — «Операционка: 120s, sequential, silent partial, orphaning edge, zero observability»

В «production-like» нагрузке (десятки задач, иногда длинный research) последовательный kilo→opencode при 120s/CLI давал 4+ минуты floor + Gemma. Реальные research runs упирались в timeout → `ok=False`, text пустой, но dispatcher **писал report** с «_Пустой ответ_» и exit metadata only in prose. Soft-fail missing CLI выглядел так же «успешным файлом». `kilocode-output.md` / `opencode-output.md` **перезаписывались** каждый run — audit dual-agent history для timestamped report утерян. Process group kill покрыл happy-path timeout; зависания вне timeout / zombie tool children / NDJSON format change → empty text, exit 0 — **ложный ok**. Ни metrics, ни structured run log, ни alerting: только stdout prints с `flush=True`.

**Механизмы:** sequential by design; default 120s too low for real research, too high for hung flaky free tier wait; no Layer A; raw paths not versioned; `ok` = returncode only, not «meaningful text»; tests don't cover subprocess; no CI E2E.

**Ранние индикаторы:** reports with empty agent sections; frequent «Timeout after 120s» in stderr field; raw files not matching report timestamp; operator runs only smoke; pytest 11 always green while E2E flaky.

**Кто страдает:** operator (debug hell); future agent (can't reconstruct run); consumers (partial reports as full).

**Класс:** **Certain / high-probability** under non-smoke load; process hygiene partially mitigated (killpg) but observability gap remains.

---

### N8 — «Success disaster: система “работает” и масштабирует плохой research в решения»

Худший конец — не crash, а **adoption**. Composer (out of scope, later) штамповал `task.md`; cron/watch гнал dispatcher±verifier; отчёты шли в wiki/киoku/PR/продуктовые решения. Free-tier + agreement theater + optional rubber-stamp judge + no citations pipeline = **высокоскоростной генератор убедительной ерунды**. Когда ошибочное решение всплыло, виновником назвали «AI research pipeline», проект похоронили с жёстким запретом «не автоматизировать research». Ирония: findings и MAP уже знали про task quality, evidence, sandbox, cost — **процесс победил бумагу**.

**Механизмы:** convenience of one command; markdown looks professional; dual-agent branding; absence of mandatory human gate; success metric = «report file exists» not «decision quality»; knowledge rot (docs/research gitignored, tickets stale vs code).

**Ранние индикаторы:** volume↑, human review time↓; reports cited in decisions without primary sources; smoke green treated as prod readiness; no golden regression set (P2-T3 empty).

**Кто страдает:** report consumers / org decisions; operator accountability; future agents (banned or blamed).

**Класс:** **Conditional** on scale/automation/organizational trust; **Speculative** timing, but mechanism is classical and fits *this* artifact shape.

---

## 2. Сводка по классам вероятности

### Certain / high-probability (при текущем дизайне, long-run)

| ID | Кратко | Почему «почти неизбежно» без смены дизайна |
|----|--------|-----------------------------------------------|
| N1 | Free-tier alias / quality collapse | Aliases hardcoded; smoke≠quality; drift в map как post-MVP |
| N2 | Phase 2 не ship → untrusted pile | HITL blockers; Phase 1 already consumable |
| N3 | Dual-agent agreement theater | Identical task, weak free models, agreement=trust |
| N7 | Ops: timeout/partial/overwrite/no observability | Код уже такой; load только проявит |

### Conditional (если automation / volume / Verifier ship)

| ID | Условие | |
|----|---------|--|
| N4 | Verifier + paid Minimax + multi-task volume, cost ceiling not hard | Cost/latency spiral |
| N5 | Unattended follow-up/watch without sandbox | Security incident |
| N6 | Judge shipped without sustained human calibration **or** Phase 1 trusted as judge-proxy | Trust collapse |
| N8 | Org scales usage into decisions | Success disaster |

### Speculative (возможно, не главный kill)

- Google/Gemma API deprecation or key loss → cross-summary dies; pipeline «ещё работает» на raw only → ещё сильнее N2.
- Hermes headless never stable → Phase 2 forever blocked (усилитель N2, не отдельная смерть).
- NDJSON schema change upstream → silent empty text with exit 0 (вариант N7; вероятность зависит от CLI vendors).
- Single VPS / single API keys wipe → total outage (availability, не «untrustworthy research»).
- Both CLIs removed from free tier same week → hard stop (visible failure, easier than silent drift).

---

## 3. Risk classes (checklist покрытия)

| Risk class | Нарратив / заметка | Severity long-run |
|------------|--------------------|-------------------|
| Free-tier model alias drift / silent quality collapse | **N1** | Kill |
| Paid judge cost spiral + false NEEDS_WORK volume | **N4** (max-1 не спасает volume) | Kill under scale |
| Security: auto/skip-permissions + automated follow-up | **N5**; flags already in Phase 1 path | Kill if automated |
| Trust: rubber-stamp or systematically wrong judge; human stops reading | **N6**; pre-judge: Gemma-as-proxy | Kill trust |
| Operational: sequential latency, timeouts, orphans, no observability | **N7**; killpg exists; audit/obs does not | Degrades → abandon |
| Knowledge rot: freeform task.md, no golden, findings/docs drift | **N2/N8**; `docs/research/` gitignored; task schema fog | Slow death |
| Dual-agent redundancy theater | **N3** | Kill epistemic value |
| Single-machine / single-key / no durable verdict audit | config env-only; raw overwrite; no verdict | Fragile + un-auditable |
| Phase 2 never ships → Phase 1 untrusted pile | **N2** | Default path |
| Success disaster: scales bad research into decisions | **N8** | Worst end-state |

---

## 4. Root mechanisms (сквозные, не по одному багу)

1. **Success metric = файл существует**, не «проверяемый research».
2. **Free generators + paid/unshipped judge** = cheap to produce, expensive or impossible to trust.
3. **Security flags required for headless** (`--auto`, `--dangerously-skip-permissions`) = prototype convenience that becomes prod attack surface under automation.
4. **Paper controls without code** (cost ceiling TBD, sandbox gate, degraded mapping TBD, alias drift later) = controls evaporate under schedule pressure.
5. **No durable provenance**: model ids, token events, raw-per-run, human overturns — почти не в артефакте.
6. **Epistemic independence assumed from process independence** (two CLIs) — false for same-class free models on same prompt.
7. **Test pyramid inverted for risk**: unit-parse green; integration/quality/security absent.

---

## 5. Leading indicators dashboard (что смотреть *до* похорон)

Игнорируемые рано, дорогие поздно:

| Signal | Где смотреть сегодня |
|--------|----------------------|
| Только smoke E2E, нет non-trivial regression task | `tasks/smoke.md` vs empty `tasks/eval/` |
| Pytest green, no pipeline CI | `tests/test_agent_cli.py` only |
| `reports/*.md` grow, zero `verdict.json` | `reports/` |
| Raw always same two filenames | `dispatcher.py` writes fixed paths |
| P2 tickets open months | `tickets/P2-*.md` status |
| Cost ceiling still «TBD» after T1/T2 | `MAP-phase2.md` Not yet specified |
| Gemma «расхождений нет» на hard tasks | cross-summary body |
| Human cites report without opening primary links | process / wiki |
| Desire to cron before docker/firejail | chat / map fog isolation |
| Model id table in HANDOFF ≠ live CLI | `HANDOFF.md` vs `agent_cli.py` defaults |

---

## 6. Top 7 kill-switches / mitigations (leverage for long-run survival)

Ранг = влияние на **выживание доверия и хоста** на 12–18 мес, не vanity features.  
Отметка **[map]** = уже частично в MAP / findings / Phase 1 code; **[gap]** = нужно ещё решить/внедрить.

| # | Mitigation | Leverage | Status |
|---|------------|----------|--------|
| **1** | **Не потреблять Phase 1 report как truth без явного human или Verifier gate.** Watermark `UNVERIFIED` / отказывать automation consumers, пока нет `verdict.json` + policy. | Режет N2, N6, N8 в корне (success disaster). | **[map]** Verifier destination; **[gap]** enforcement & cultural gate |
| **2** | **Hard isolation before any unattended follow-up/watch** (container / limited user / no secrets mount). Map уже gate — **не нарушать**. | Единственный hard stop для N5. | **[map]** explicit; **[gap]** design not specified |
| **3** | **Numeric cost + wall-time ceiling per Verifier cycle** (env hard fail, analogous to `CLI_TIMEOUT`), incl. dual-CLI follow-up. Lock in P2-T1/T2, not «later». | Убивает N4; без этого paid judge = suicide at volume. | **[map]** required TBD; **[gap]** numbers + code |
| **4** | **Pin or contract-test research models** (record resolved model/backend if CLI exposes it; golden task quality smoke beyond `pong`; alert on empty/short/timeout rate). | Прямой контр N1 + часть N7. | **[map]** fog post-MVP; **[gap]** almost entirely |
| **5** | **Layer A + durable audit before Layer B spend:** fail closed on dual-empty / both failed; version raw outputs per run id; persist model ids, exit, timing, tokens if present; never overwrite sole raw path. | Делает N7 visible; cheap; enables any later judge. | **[map]** Layer A ticket P2-T4, verdict.json in findings; **[gap]** not coded; raw overwrite still live |
| **6** | **Eval corpus + ongoing human↔verdict agreement (P2-T3/T6), with false APPROVED as primary red line.** Ship Verifier only if beats «human skims Gemma §3». | Единственная страховка от N6 и бессмысленного N4. | **[map]** destination «eval’d» + findings §4.6; **[gap]** corpus empty, HITL |
| **7** | **Task quality bar + anti-theater epistemic rules:** structured `task.md` acceptance bullets; treat dual agreement as *weak* signal; require evidence/gaps in report or BLOCKED; degraded mode when one CLI dies (no silent full report). Optional: drop dual free-CLI for one stronger path if agreement always noise. | Бьёт N3, слабые task→judge noise, partial lies. | **[map]** degraded rule to encode; Composer/task fog; findings task quality; **[gap]** no schema, no degraded code |

### Что уже есть и *не* хватает как kill-switch

| Уже есть | Почему недостаточно long-run |
|----------|------------------------------|
| `os.killpg` on timeout | Не лечит exit0+empty, format drift, hung tools outside timeout budget story |
| Soft-fail missing CLI | Превращает missing tool в «report file» без hard fail |
| Max 1 follow-up (paper) | Не caps **N tasks** or $ |
| Prefer false NEEDS_WORK (paper) | Без cost ceiling и task bar → burnout (N4) |
| Process sequential simplicity | Latency floor; not a trust control |
| NDJSON unit tests | Local correctness ≠ pipeline trust |

### Явно *не* в top-7 (низкий leverage сейчас)

- Parallel `asyncio.gather` (latency only; map agrees).
- Full VeriMAP DAG / multi-round MAD (findings: scale mismatch).
- Gemma-as-Layer-B (rejected; self-enhancement).
- Level 2 `kilo serve` / `opencode serve` before isolation + quality gates.
- Framework shopping (DeepEval spike) without eval corpus.

---

## 7. Одноабзацный «cause of death» (если выбрать одну формулировку)

**research-pipeline умер не от падения smoke-теста, а от того, что научился дёшево производить убедительные markdown-отчёты двух free headless coding-CLI с permission-skip, без durable provenance, без numeric cost/isolation gates, и (скорее всего) без shipped Verifier — после чего либо люди перестали верить папке `reports/`, либо хуже: поверили и масштабировали ошибку.**

---

## 8. Uncertainty notes

- Сроки смерти Phase 2 (N2) vs security (N5) vs cost (N4) зависят от поведения operator'а, не от кода — **условные** ветки помечены.
- Качество free backends на горизонте 12–18 мес **неизвестно**; N1 утверждает *silent change risk*, не «модели всегда плохи».
- Sorting-comparison в `research/` показывает, что **executable** research в экосистеме возможен; premortem бьёт в *automated dual-CLI essay path*, не в любой research на машине.
- Premortem **не** утверждает, что Phase 1 бесполезен как прототип CLI wiring — утверждает, что **long-run production-like use** текущего design/path убийственен без kill-switches §6.

---

*Read-only premortem. No code fixes, no ticket resolves, no commit implied.*
*Primary sources in-repo: `MAP.md`, `MAP-phase2.md`, `CONTEXT.md`, `HANDOFF.md`, `dispatcher.py`, `agent_cli.py`, `gemma.py`, `config.py`, `tickets/P2-*.md`, `docs/research/verifier-phase2-findings.md`, `reports/`, `tests/test_agent_cli.py`.*
