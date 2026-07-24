# Research: Verifier for research-pipeline (Phase 2)

**Date:** 2026-07-23  
**Status:** primary-source review (rewritten; replaces earlier marketing-style draft)
**Reviewer pass:** 2026-07-24 — sequential wording, MAD caveat framing, merge/append, threshold TBD, OpenAI launch URL, STORM phrasing, “delta task” retired  
**Audience:** whoever charts / builds Phase 2 Verifier  
**Scope of this note:** what the literature *actually* says, what transfers to *this* repo, what does not.

---

## 0. Context: what we already have

Current Dispatcher (Phase 1, done):

```
task.md → Kilocode then Opencode (sequential CLI runs; independent second opinion)
       → raw outputs
       → Gemma 4 31B cross-summary (common / diffs / watch-outs)
       → report-*.md
```

Planned Phase 2 (from `MAP.md`): check report quality; optional re-research loop.  
Planned arbiter: **Minimax via Hermes** (project note, not a literature requirement).

Gemma already does a soft “second look” (cross-summary). A Verifier is only worth building if it adds **decision + action** (verdict + optional targeted follow-up (gap task)), not another free-form essay.

---

## 1. Primary sources (facts only)

### 1.1 Anthropic — Evaluator–Optimizer workflow

| | |
|--|--|
| **Source** | Anthropic Engineering, *Building effective agents*, 19 Dec 2024 |
| **URL** | https://www.anthropic.com/engineering/building-effective-agents |

**What the post states:**

- Workflow: one LLM generates; another evaluates and gives feedback; loop until a stop condition.
- **When it fits:** clear evaluation criteria; iterative refinement provides measurable value.
- Two fitness signs: (1) human feedback would improve the draft; (2) an LLM can give that kind of feedback.
- Broader principle of the whole post: start simple; add multi-step complexity only when it **demonstrably** helps.
- Agents/workflows should have **stopping conditions** (e.g. max iterations) — no fixed `N=1` mandate.

**Not claimed:** fixed single re-run as SOTA; named “Delta-Tasking”; token-savings percentages.

---

### 1.2 OpenAI — Deep Research (product + API)

| | |
|--|--|
| **API guide** | https://developers.openai.com/api/docs/guides/deep-research |
| **Launch note** | OpenAI, *Introducing deep research*, Feb 2025 — https://openai.com/index/introducing-deep-research/ |

**What OpenAI documents:**

- Deep research models browse/search and synthesize multi-source reports (analyst-style).
- **ChatGPT product path** (three steps):
  1. **Clarification** (smaller model gathers intent/context),
  2. **Prompt rewriting** (expanded research brief),
  3. **Deep research** (heavy model + tools).
- **API path:** no built-in clarify/rewrite — you must pass a fully-formed prompt; optional pre-steps are on the developer.
- Cost/latency control: `max_tool_calls` bounds tool use; long runs → background mode / webhooks; high timeouts.
- Output includes tool traces (`web_search_call`, etc.) and **inline citations** with annotations — designed for evidence, not post-hoc scoring of someone else’s report.
- Private data: file_search / MCP with search+fetch interface; security notes on prompt injection / exfiltration.

**What this is *not*:** a separate “Verifier agent” over dual CLI reports. It is an **in-loop research agent** with search tools.

**Useful takeaway for us:** quality of research tasks is heavily gated by **task specificity** (clarify + rewrite). Weak `task.md` → weak reports → verifier noise. Composer / task quality may matter more than a fancy judge.

---

### 1.3 Stanford STORM

| | |
|--|--|
| **Paper** | Shao et al., *Assisting in Writing Wikipedia-like Articles From Scratch…*, arXiv:2402.14207 (NAACL 2024) |
| **Name** | **STORM** = *Synthesis of Topic Outlines through Retrieval and **Multi-perspective Question Asking*** (not “Conversation”) |
| **Code/overview** | https://github.com/stanford-oval/storm |

**What the paper states:**

- Focus is **pre-writing**: discover perspectives → simulate multi-perspective Q&A grounded on sources → curate outline → write long article.
- Evaluation (FreshWiki): vs outline-driven RAG baseline, STORM articles more often judged **organized** (by a 25% absolute increase) and **broader in coverage** (by 10%) — *those numbers are about STORM vs their baseline*, not about verification loops.
- Expert feedback highlights hard problems: **source bias transfer**, **over-association of unrelated facts**.

**What this is *not*:** post-hoc verification, delta re-research, or cross-model auditing.

**Useful takeaway for us:** multi-perspective coverage is a **generation-time** design (how you ask research agents). For Verifier: check *coverage of perspectives/sub-questions* if `task.md` enumerates them — do not pretend STORM invented a re-research loop.

---

### 1.4 VeriMAP — verification-aware planning

| | |
|--|--|
| **Paper** | Xu, Zhang, Mitra, Hruschka, *Verification-Aware Planning for Multi-Agent Systems*, arXiv:2510.17109 (Oct 2025; EACL 2026 listing) |
| **PDF/HTML** | https://arxiv.org/abs/2510.17109 |

**What VeriMAP actually is:**

- Multi-agent system with **Planner, Executor, Verifier, Coordinator**.
- Planner builds a **DAG of subtasks** and, for each node, emits **Verification Functions (VFs)** as *acceptance criteria before execution finishes*:
  - **Python VFs** — deterministic asserts (type/format/functional checks);
  - **NL VFs** — semantic checks judged by an LLM.
- Executors produce **structured I/O** (named JSON fields); handoff failures (wrong format / wrong interpretation) are first-class, not only “wrong answer.”
- Verifier: **AND** over VFs (any fail → fail); feedback from traceback (Python) or NL explanation (LLM).
- Coordinator: retries per node (default **3**), then **replanning** (default up to **5** plan iterations).
- Empirically: planner-defined VFs beat “generic LLM verify the instruction” (**MAP-V**); replanning helps more when VFs are informative.
- **Cost:** higher than single ReAct; on hard tasks the cost gap to weaker multi-agent variants narrows because retries pay off; on easy tasks verification overhead is less justified.
- **VF error modes (important):**
  - Generic MAP-V: often **loose** → high **false positives** (bad output marked OK).
  - VeriMAP: often **stricter** → lower FP, sometimes higher **false negatives** (good output rejected) on coding tasks.
- Limitations (authors): centralized planner quality bottleneck; replan signal design is crude; not free on resources.

**What VeriMAP is *not*:** “use a different model family as cross-auditor of two free-form reports.” Cross-model auditing is not the core contribution.

**Useful takeaway for us:** the portable idea is **acceptance criteria attached to the task**, preferably mix of **programmatic + semantic** checks — not copying the full DAG planner.

---

### 1.5 Multi-agent debate (factuality)

| | |
|--|--|
| **Paper** | Du, Li, Torralba, Tenenbaum, Mordatch, *Improving Factuality and Reasoning in Language Models through Multiagent Debate*, arXiv:2305.14325 (May 2023) |

**What the paper states:**

- Multiple model **instances** propose answers, then **read/critique peers** over rounds and update; final consensus-style answer.
- Aimed at reasoning + factual validity; reduces some fallacious answers vs single-shot.

**Caveats often claimed in follow-on MAD work** (not re-verified primary-source-by-primary-source in this note — **do not base design gates on these until cited**):

- Gains may not beat cheaper single-agent baselines (CoT / self-consistency) in every setting.
- Heterogeneous models may help more than same-model clones.
- Extra rounds may over-deliberate (shared mistakes reinforced).
- Sycophancy between agents can collapse useful disagreement.

**Useful takeaway grounded in Du et al. + our codebase:** we already run **two independent CLI drafts** (different tools/models). A Verifier should **surface disagreement**, not force artificial consensus. Prefer a **separate judge path** (e.g. Hermes/Minimax) over same-family self-critique of Gemma’s summary.

---

### 1.6 Self-Refine

| | |
|--|--|
| **Paper** | Madaan et al., *Self-Refine: Iterative Refinement with Self-Feedback*, arXiv:2303.17651 (NeurIPS 2023) |

**What it states:**

- Same LLM: generate → feedback → refine, iterate; no extra training.
- Works better when feedback is **specific and actionable**.

**Implication:** pure self-refine on Gemma’s own summary is weak insurance (same family, self-enhancement risk). Prefer **other model** + **external criteria** (task.md, structured checks).

---

### 1.7 LLM-as-a-Judge biases

| | |
|--|--|
| **Paper** | Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, arXiv:2306.05685 (NeurIPS 2023) |

**What it states:**

- Strong LLM judges can approach **~human–human agreement** on preference tasks (~80% in their setup) — *not* a blank check for research factuality.
- Documented biases: **position** (order of candidates), **verbosity** (longer looks better), **self-enhancement** (prefer own family), limited reasoning on hard checks.
- Mitigations discussed in the line of work: rubrics, position swaps, hide model identities, penalize empty length, etc.

**Implication for us:** never pass “Kilocode report first, Opencode second” in a fixed order without randomization/swap; score against **task checklist**, not “which essay is nicer”; do not ask the judge to invent ground truth for open-web facts without evidence.

---

## 2. Myths from the previous draft (explicitly closed)

| Claim in old doc | Reality |
|------------------|---------|
| “Delta-Tasking” is a named SOTA pattern from OpenAI/STORM | **No primary source** uses this name for a standard pattern. Targeted follow-up tasks are a *reasonable engineering idea*, not a cited SOTA brand. |
| “Saves up to 70% tokens” / “Context Debt” as established metric | **No citation found** in the sources above. Do not treat as fact. |
| Anthropic requires **N=1** iteration budget | Anthropic requires **clear criteria + a stop condition**. `N=1` may be *our* cost cap, not their rule. |
| STORM = multi-perspective **conversation** + verification loop | Acronym is **Question Asking**; system is pre-writing/outline, not a verifier loop. |
| VeriMAP = cross-model auditing with Hermes/Minimax | VeriMAP = **planner-defined VFs + structured handoffs + coordinator retries/replan**. |
| OpenAI Deep Research proves post-hoc dual-report verification | Deep Research is **tool-using research generation**, not our architecture. |

---

## 3. What actually transfers to *this* pipeline

### Already partially covered

| Need | Current coverage |
|------|------------------|
| Independent second opinion | Two CLIs (Kilo + Opencode) |
| Diff / tension surface | Gemma cross-summary section “расхождения” + “на что обратить внимание” |
| Human-readable report | `report-*.md` |

### Gaps a Verifier should own (literature-aligned)

| Gap | Why (source-backed) |
|-----|---------------------|
| **Binary/actionable verdict** | Evaluator–optimizer needs criteria + stop, not only prose (Anthropic). |
| **Criteria tied to `task.md`** | Acceptance criteria beat free-form “does this look good?” (VeriMAP vs MAP-V). |
| **Programmatic checks where possible** | Empty outputs, both agents failed, missing sections, length floors, parse errors — free and unbiased (VeriMAP Python VFs; Anthropic simplicity). |
| **Structured gap list → follow-up task** | Self-Refine / evaluator feedback must be **specific**; vague “improve quality” fails. |
| **Cap on loops** | Anthropic stop conditions; VeriMAP retry/replan caps; debate over-deliberation risk. |
| **Judge ≠ generator family** | Self-enhancement / self-refine limits; MAD heterogeneity helps. |
| **Order / verbosity bias control** | LLM-as-Judge (Zheng et al.). |
| **Task quality upstream** | OpenAI clarify/rewrite; STORM multi-perspective pre-writing — bad tasks waste verifiers. |

### What *not* to port (scale mismatch)

- Full **VeriMAP DAG planner** with per-subtask Python VFs and replan-5 — overkill for “two CLIs + summary”.
- Full **multi-round MAD** among many agents — expensive; we already have two independent drafts.
- Cloning **Deep Research** tool loop inside Verifier — wrong role (generation vs check).
- Claiming factual ground truth from the judge alone without sources — judges fail at open-ended fact checking (bias papers + STORM source-bias notes).

---

## 4. Design implications (proposal, not “SOTA”)

These are **engineering recommendations** derived from §1–3 for *our* codebase. They are not mandated by any single paper.

### 4.1 Role split

```
task.md
   │
   ▼
Dispatcher (as today)
   │  report.md = raw_A + raw_B + cross_summary
   ▼
Verifier (Hermes / Minimax or other non-Gemma path)
   │  inputs: task.md + report.md (+ optional raws)
   │  outputs: structured Verdict
   │
   ├─ APPROVED  → final_report.md (tag + criteria scores)
   └─ NEEDS_WORK → task_followup.md (only listed gaps)
                      │
                      ▼
                 Dispatcher once more (same pipeline or subset)
                      │
                      ▼
                 Append `## Follow-up` (+ optional re-summary) → final_report.md
                 (hard stop: max 1 follow-up run by default)
```

**Merge vs append:** MVP default is **append** second-pass material under `## Follow-up` (cheap, auditable). True dual-pass **merge** of agent material is a later upgrade, not required for destination.

**Rationale:** evaluator–optimizer shape (Anthropic) + capped iteration (stop condition) + specific feedback (Self-Refine / VeriMAP).  
**Default max follow-up = 1** is a *cost policy* for a prototype, not Anthropic’s rule. Raise only if measured quality gain pays for 2× CLI cost.

### 4.2 Two layers of checks (VeriMAP lesson, simplified)

**Layer A — cheap, code-only (no LLM)**

Examples:

- Non-empty agent outputs; exit codes.
- At least one agent succeeded.
- Report contains required section headers (if we standardize format).
- Cross-summary present if `GOOGLE_API_KEY` set.
- Optional: min char length per agent for non-smoke tasks.

Fail Layer A → **HARD_FAIL** (no LLM spend) or auto-retry CLI once.

**Layer B — semantic rubric (LLM judge, structured JSON)**

Score only dimensions you can define from `task.md`. Start minimal:

| Dimension | Question | Scale |
|-----------|----------|--------|
| `task_coverage` | Are the *explicit* questions/topics in task.md addressed? | 0–2 or pass/fail + missing list |
| `disagreement_handling` | Does the report surface real A/B conflicts (or correctly note agreement)? | pass/fail + notes |
| `evidence_quality` | Are non-trivial claims backed by named sources / methods / numbers when the task needs them? | 0–2 + gaps |
| `actionable_gaps` | What *specific* follow-ups would close remaining holes? | free list (required if not APPROVED) |

**Verdict rule (proposal — thresholds to lock in Phase 2 grilling):**

Temporary defaults until grilling:

- `APPROVED` if Layer A pass AND Layer B has **no failed required checks** AND `missing[]` / `actionable_gaps` is empty.
- `NEEDS_WORK` if gaps are specific and fixable by one more research pass (judge must list them).
- `BLOCKED` if judge sets `task_underspecified: true` (OpenAI clarify lesson) — don’t burn re-research; flag human/Composer.

**TBD in grilling:** which Layer B dimensions are required vs optional; score 0–2 cutoffs; whether false APPROVED is worse than false NEEDS_WORK (strictness).

Avoid a single opaque “quality: 7/10”. Prefer **checklists + missing items** (VeriMAP acceptance criteria spirit; lower false-positive “looks fine”).

### 4.3 Follow-up task generation

When `NEEDS_WORK`:

- Write `task_followup.md` that contains **only** gap items (not “rewrite entire report”).
- Prefer questions that a research agent can answer with tools (benchmarks, citations, missing case).
- Do **not** re-send full original task + “also fix quality” — dilutes focus (Self-Refine: specific feedback wins).
- After follow-up, **merge** new material into final report; don’t discard first pass (preserves dual-agent diversity).

Naming: call this **targeted follow-up** or **gap task** in our docs. Avoid inventing fake SOTA brands.

### 4.4 Judge model choice

| Option | Pros | Cons |
|--------|------|------|
| Same Gemma as summarizer | Simple | Self-enhancement / same blind spots |
| Hermes + Minimax (MAP note) | Heterogeneous critic; project already has Hermes | Need headless CLI research (like T2) |
| Strong external API judge | Often better agreement with humans on prefs | Cost, keys, privacy |

**Recommendation:** keep MAP preference (Hermes/Minimax) **if** headless path is reliable; otherwise any **non-Gemma** path is the real requirement. Structured output (JSON schema) > free markdown for machine gating.

### 4.5 Bias hygiene for the judge prompt

- Pass agents as **Agent A / Agent B** without brand preference language; optionally **swap order** on a second judge pass if high-stakes.
- Instruct: prefer coverage of task bullets over essay length (anti-verbosity).
- Instruct: if you cannot verify a claim, mark **unverified**, do not invent confirmation.
- Include `task.md` text as the source of truth for coverage — not the judge’s world knowledge alone.

### 4.6 Evaluation plan (so we know if Verifier helps)

Without this, Anthropic’s “only add complexity when measurable” is ignored.

1. Collect **5–10 real tasks** (not smoke `pong`).
2. Human labels: APPROVE / NEEDS_WORK + which gaps matter.
3. Compare:  
   - baseline = report as today;  
   - + Layer A only;  
   - + Layer A+B;  
   - + one follow-up when NEEDS_WORK.
4. Metrics that matter here:  
   - human agreement with verdict;  
   - fraction of false APPROVED (dangerous);  
   - extra CLI cost;  
   - whether follow-up actually closed listed gaps.

If Layer B does not beat “human skims Gemma section 3”, **do not ship the loop**.

---

## 5. Suggested MVP (smallest useful Verifier)

1. **Layer A** programmatic gate in Python (same repo as dispatcher).
2. **Layer B** one structured LLM call: JSON verdict + `missing[]` + `followup_prompt`.
3. Wire: if NEEDS_WORK and `followup_enabled`, run dispatcher once on `task_followup.md`, append section `## Follow-up` to final report.
4. No replan DAG, no multi-round debate, no second cross-summary model required for MVP.
5. Persist `verdict.json` next to `report-*.md` for audit.

This is enough to test the hypothesis: *acceptance criteria + one targeted re-run improve research reports enough to justify cost.*

---

## 6. Open questions (for Phase 2 map / grilling)

Not answered by literature alone — need product decisions:

1. What is “good enough” for *your* tasks (internal notes vs publishable research)?
2. Is false APPROVED worse than false NEEDS_WORK? (sets strictness / thresholds)
3. Should follow-up re-run **both** CLIs or only the weaker / one cheaper model?
4. Who owns underspecified tasks — Verifier `BLOCKED` vs Composer rewrite?
5. Final artifact: overwrite report vs `final_report.md` + keep intermediates?
6. Hermes headless: command surface, model id, timeout, auth (needs its own research ticket like T2).

---

## 7. Sources (canonical)

1. Anthropic — *Building effective agents* (2024-12-19)  
   https://www.anthropic.com/engineering/building-effective-agents  
2. OpenAI — Deep research API guide  
   https://developers.openai.com/api/docs/guides/deep-research  
3. Shao et al. — STORM, arXiv:2402.14207  
   https://arxiv.org/abs/2402.14207  
4. Xu et al. — VeriMAP, arXiv:2510.17109  
   https://arxiv.org/abs/2510.17109  
5. Du et al. — Multiagent Debate, arXiv:2305.14325  
   https://arxiv.org/abs/2305.14325  
6. Madaan et al. — Self-Refine, arXiv:2303.17651  
   https://arxiv.org/abs/2303.17651  
7. Zheng et al. — LLM-as-a-Judge / MT-Bench, arXiv:2306.05685  
   https://arxiv.org/abs/2306.05685  

Secondary (optional later): Stechly et al. self-verification limits (arXiv:2402.08115); VeriLA human-centered agent failure analysis (arXiv:2503.12651); Cemri et al. multi-agent failure modes (arXiv:2503.13657).

---

## 8. Supersedes

This document **supersedes** `docs/verifier-sota-architecture-2026.md` (2026-07-23 draft). That file mixed real names with uncited patterns (“Delta-Tasking”, “70% tokens”) and mis-labeled STORM/VeriMAP. Prefer this file for any Phase 2 decision work.
