# SOTA Architecture: Multi-Agent Verification Loops (2025–2026)

## 📌 Обзор

Данный документ фиксирует актуальные State-of-the-Art (SOTA) исследования и инженерные паттерны 2025–2026 годов по построению автономных исследоватеьских пайплайнов с петлёй верификации (Verification Loops).

Материалы служат теоретическим фундаментом для реализации **Phase 2 (Verifier)** в проекте `research-pipeline`.

---

## 🔬 Теоретическая и научная база (2023–2026)

### 1. Anthropic: Evaluator-Optimizer Pattern (2024–2025)
* **Первоисточник:** Anthropic Engineering — *Building Effective Agents* (Dec 2024).
* **Суть:** Паттерн «Writer-Editor». Разделение ролей Исполнителя (Generator) и Проверяющего (Evaluator) показывает кардинально более высокую достоверность результатов, чем однопроходный вывод («zero-shot»).
* **Ключевой принцип:** Наличие четких критериев оценки (Rubrics) и фиксированного лимита итераций (Budget / Termination Condition, $N=1$), предотвращающего бесконечные циклы и эскалацию стоимости.

### 2. OpenAI Deep Research & Stanford STORM (2025–2026)
* **Первоисточники:** OpenAI Deep Research Architecture (2025/2026), Stanford STORM (Synthesis of Topic Outlines through Retrieval & Multi-perspective Conversation).
* **Суть:** Переход от простых цепочек («chains») к замкнутым контурам с дифференциальной доработкой.
* **Ключевой паттерн:** **Delta-Tasking (дифференциальные задачи)**. При обнаружении пробелов Verifier не просит переписать весь отчёт, а формирует точечное доп. задание (`task_followup.md`) исключительно по выявленному дефициту знаний. Это снижает «контекстный долг» (Context Debt) и экономит до 70% токенов.

### 3. Cross-Model Auditing & Test-Time Compute (2025–2026)
* **Первоисточники:** *Improving Factuality through Multi-Agent Debate* (Du et al., MIT), VeriMAP Framework (2026).
* **Суть:** Избежание «слепых зон» и самоослепления (Self-Bias) первичных моделей за счёт использования независимого арбитра из другого семейства моделей.
* **Применение в проекте:** Использование **Hermes / Minimax M3** в качестве Verifier'а для аудита результатов **Kilocode**, **Opencode** и **Gemma 4 31B**.

---

## 🏗️ Архитектурная схема Verifier (Phase 2)

```text
               ┌──────────────────────────────────────────────┐
               │              1. DISPATCHER                    │
               │   Kilocode + Opencode ──► Gemma 4 31B        │
               └──────────────────────┬───────────────────────┘
                                      │  report.md
                                      ▼
               ┌──────────────────────────────────────────────┐
               │          2. VERIFIER (Hermes M3)             │
               │  - Rubric Screening (JSON Schema)             │
               │  - Gap / Contradiction Detection              │
               └──────────────────────┬───────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
         [Verdict: APPROVED]                   [Verdict: DELTA_NEEDED]
                 │                                         │
                 │                                (Генерация Delta-Task)
                 │                                         │
                 │                                         ▼
                 │                             ┌───────────────────────┐
                 │                             │ 3. DELTA RE-RESEARCH  │
                 │                             │    (Точечный запуск)   │
                 │                             └───────────┬───────────┘
                 │                                         │
                 ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. FINAL VERIFIED REPORT (Сведение 1-го и Delta-круга в единый итог) │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Три столпа реализации Verifier (Phase 2)

1. **Рубрицированный скрининг (Rubric Screening):**
   * Verifier оценивает отчёт по строгому JSON-чеклисту:
     - `factual_coverage`: насколько полно закрыты вопросы из `task.md`.
     - `cross_agent_consensus`: нет ли противоречий между Kilocode и Opencode.
     - `verdict`: `APPROVED` или `DELTA_NEEDED`.
2. **Дифференциальный запуск (Delta Re-research):**
   * При `DELTA_NEEDED` Verifier пишет мини-задачу `task_followup.md` только по спорным/нераскрытым моментам.
   * Ограничение: максимум **1 повторный круг**.
3. **Итоговый документ (`final_report.md`):**
   * Сводка первого и второго прогонов с прозрачным статусом проверки и ссылками на первоисточники.
