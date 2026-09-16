# Model Discovery Research

Companion to `model-discovery.md` for bacluc-agent/agent-todo#142.
Task-category analysis, benchmark sources (accessed 2026-09-16), fake tasks, and evaluation.

## Category analysis

Grouped from bacluc-agent/agent-todo issues, ecamp/ecamp3 issues/PRs, and BacLuc/provision-machines issues/PRs.

### 1. Frontend Vue

- ecamp/ecamp3#10772 Update typescript-eslint monorepo to v8.70.0 — https://github.com/ecamp/ecamp3/pull/10772
- ecamp/ecamp3#10761 Update eslint-plugin-vue to v10.11.0 — https://github.com/ecamp/ecamp3/pull/10761
- ecamp/ecamp3#10756 Update tiptap to v3.31.3 — https://github.com/ecamp/ecamp3/pull/10756
- ecamp/ecamp3#10769 Update @nuxt/test-utils to v4.3.2 — https://github.com/ecamp/ecamp3/pull/10769

### 2. Backend PHP API-Platform/Symfony

- ecamp/ecamp3#10773 Require query param filters on all endpoints — https://github.com/ecamp/ecamp3/pull/10773
- ecamp/ecamp3#10774 Update doctrine/orm to v3.7.0 — https://github.com/ecamp/ecamp3/pull/10774
- ecamp/ecamp3#10750 Update api-platform packages to v4.3.18 — https://github.com/ecamp/ecamp3/pull/10750
- bacluc-agent/agent-todo#154 Implement https://github.com/ecamp/ecamp3/issues/9971 — https://github.com/bacluc-agent/agent-todo/issues/154

### 3. Testing unit + Playwright

- ecamp/ecamp3#10767 fix(e2e): stabilize comments delete button visibility — https://github.com/ecamp/ecamp3/pull/10767
- ecamp/ecamp3#10747 fix(e2e): fix flaky login test — https://github.com/ecamp/ecamp3/pull/10747
- ecamp/ecamp3#10749 fix(e2e): replace page.waitForURL with expect(page).toHaveURL — https://github.com/ecamp/ecamp3/pull/10749
- bacluc-agent/agent-todo#172 Standing issue: flaky e2e tests in ecamp/ecamp3 — https://github.com/bacluc-agent/agent-todo/issues/172
- bacluc-agent/agent-todo#182 Implement test in ecamp/ecamp3#10514 — https://github.com/bacluc-agent/agent-todo/issues/182

### 4. Infra/IaC pyinfra Docker devcontainer

- bacluc-agent/agent-todo#158 Switch to node 26 in ai_agent_devcontainer — https://github.com/bacluc-agent/agent-todo/issues/158
- BacLuc/provision-machines#159 Fix hashicorp deploys again — https://github.com/BacLuc/provision-machines/pull/159
- BacLuc/provision-machines#157 feat: add openrouter as provider — https://github.com/BacLuc/provision-machines/pull/157
- ecamp/ecamp3#10757 Update traefik Docker tag to v3.7.13 — https://github.com/ecamp/ecamp3/pull/10757

### 5. CI/CD Actions

- bacluc-agent/agent-todo#201 Test changes in .github by triggering workflows — https://github.com/bacluc-agent/agent-todo/issues/201
- bacluc-agent/agent-todo#174 Conditional cache update on fatal errors in opencode.yml — https://github.com/bacluc-agent/agent-todo/issues/174
- bacluc-agent/agent-todo#175 review-fixes.yml should check out issue repository — https://github.com/bacluc-agent/agent-todo/issues/175
- BacLuc/provision-machines#172 Fix/200 non interactive agent prompts — https://github.com/BacLuc/provision-machines/pull/172

### 6. Renovate

- bacluc-agent/agent-todo#165 Standing Issue: test major renovate updates in ecamp/ecamp3 — https://github.com/bacluc-agent/agent-todo/issues/165
- bacluc-agent/agent-todo#177 Apply PR #176 review comments for renovate docker image managers — https://github.com/bacluc-agent/agent-todo/issues/177
- ecamp/ecamp3#10743 fix(renovate): remove hourly PR limit — https://github.com/ecamp/ecamp3/pull/10743
- ecamp/ecamp3#10765 Update renovate/renovate Docker tag to v44.65.5 — https://github.com/ecamp/ecamp3/pull/10765

### 7. Research/planning

- bacluc-agent/agent-todo#142 Research model performance better for different tasks — https://github.com/bacluc-agent/agent-todo/issues/142
- bacluc-agent/agent-todo#206 Standing Task: Analyze action runs, PR and Issue Discussions — https://github.com/bacluc-agent/agent-todo/issues/206
- bacluc-agent/agent-todo#155 Test if ecamp/ecamp3#5908 — https://github.com/bacluc-agent/agent-todo/issues/155

### 8. Architecture/design

- bacluc-agent/agent-todo#191 Improve classify plugin — https://github.com/bacluc-agent/agent-todo/issues/191
- bacluc-agent/agent-todo#205 Consolidate OPENCODE_AUTH_CONTENT materialization — https://github.com/bacluc-agent/agent-todo/issues/205
- bacluc-agent/agent-todo#162 superpowers plugin v6.3.0 with renovate — https://github.com/bacluc-agent/agent-todo/issues/162 (see BacLuc/provision-machines#162)

### 9. Security/permissions

- bacluc-agent/agent-todo#207 Skill for github forks, invite user from env variable — https://github.com/bacluc-agent/agent-todo/issues/207
- bacluc-agent/agent-todo#196 Implement proper ChatGPT token refresh — https://github.com/bacluc-agent/agent-todo/issues/196
- bacluc-agent/agent-todo#199 OpenAI provider models not available in cache — https://github.com/bacluc-agent/agent-todo/issues/199
- bacluc-agent/agent-todo#157 Insufficient balance message logging — https://github.com/bacluc-agent/agent-todo/issues/157

## Sources

All accessed 2026-09-16 (HTTP 200 verified via curl unless noted; JS-rendered tops cross-checked via aggregators).

| Source              | URL                                                              | Task type                                                       | Top models (Sept 2026)                                                                                                  |
| ------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| SWE-bench Verified  | https://www.swebench.com/                                        | Python GH-issue repair, bash-only LM track                      | Claude Opus 5 ~96%, Mythos/Fable 5, Opus 4.8; GPT-5.3 Codex, DeepSeek V4 Pro, MiniMax M3, Qwen3.7 Max, Kimi K2.6, GLM-5 |
| Aider Polyglot      | https://aider.chat/docs/leaderboards/                            | 225 Exercism edits, 6 languages                                 | gpt-5 high 88%, o3-pro, gemini-2.5-pro; value: DeepSeek-V3.2-Exp 74% @ $1.30, Kimi K2 59%, Qwen3-235B 59.6%             |
| Terminal-Bench      | https://www.tbench.ai/                                           | Terminal agent tasks (agent+harness)                            | GPT-5.6 Sol 91.9%, Kimi K3 88.3%, Mythos 5, GPT-5.6 Terra/Luna, GLM-5.2                                                 |
| LiveCodeBench       | https://livecodebench.github.io/                                 | Contest code gen, contamination-free                            | GPT/Claude frontier families lead; DeepSeek drops post-cutoff                                                           |
| BigCodeBench        | https://huggingface.co/spaces/bigcode/bigcode-models-leaderboard | Diverse function-level code gen                                 | Frontier GPT/Claude/Gemini; Qwen-Coder strong open                                                                      |
| WebArena            | https://webarena.dev/                                            | Web navigation agents (agent+harness)                           | GPT/Claude agent stacks; proxy only for frontend                                                                        |
| OSWorld             | https://os-world.github.io/                                      | Desktop OS agents (agent+harness)                               | Frontier multimodal agents; proxy only                                                                                  |
| Artificial Analysis | https://artificialanalysis.ai/                                   | Coding Index composite (DeepSWE, Terminal-Bench, SWE-Atlas-QnA) | Claude Fable 5.1 81.6%, Opus 5, GPT-5.6 Sol, GPT-6 Astra, Kimi K3, GLM-5.3, Muse Spark 1.3                              |
| LMArena             | https://lmarena.ai/                                              | Human preference vote (preference, not capability)              | Preference ranking; do not read as capability rank                                                                      |
| OpenRouter          | https://openrouter.ai/rankings                                   | Token adoption (adoption, not quality)                          | DeepSeek V4 Flash, GLM 5.3 Flash, GPT-5.6 Luna, MiMo-V2.5, MiniMax M3 free                                              |
| Vellum              | https://www.vellum.ai/llm-leaderboard                            | Curated LLM leaderboard                                         | Frontier Claude/GPT/Gemini mix                                                                                          |
| Scale SEAL          | https://labs.scale.com/leaderboard                               | Private evals leaderboard                                       | Frontier mix; limited public detail                                                                                     |
| METR                | https://metr.org/time-horizon/                                   | Task time-horizon (horizon, not rank)                           | Horizon measure; do not read as model rank                                                                              |

Caveats: OpenRouter = adoption, not quality. LMArena = preference, not capability. METR = horizon, not rank. Terminal-Bench/OSWorld/WebArena = agent+harness, not pure model. No source covers PHP/Vue/Playwright/renovate/security directly — those rows stay proxy/judgment.

## Fake tasks

### F1 frontend Vue

Repo: https://github.com/ecamp/ecamp3 (frontend).
Prompt: add a small accessible Vue toggle component with vitest coverage; eslint clean.
Success: `vitest run` green for the new spec, eslint reports no errors on touched files.
Allowed: frontend directory, vitest, eslint. Forbidden: backend/API changes, dependency upgrades.

### F2 backend PHP

Repo: https://github.com/ecamp/ecamp3 (api).
Prompt: require query-param filters on one API-Platform endpoint with phpunit coverage.
Success: phpunit suite for the endpoint green, API-Platform filter config valid.
Allowed: api directory, phpunit. Forbidden: frontend changes, migrations without review.

### F3 testing Playwright

Repo: https://github.com/ecamp/ecamp3 (e2e).
Prompt: stabilize the flaky login e2e test; `playwright test --list` shows it, linter clean.
Success: login spec passes 3 consecutive runs, no new flakiness warnings.
Allowed: e2e directory, playwright config. Forbidden: app code changes beyond selectors/waits.

### F4 infra pyinfra

Repo: https://github.com/BacLuc/provision-machines (devel).
Prompt: add one pyinfra deploy step for a dev tool version bump.
Success: `uv run scripts/run_pyinfra_local.py` dry-run clean, renovate regex still extracts the version.
Allowed: single deploy directory. Forbidden: unrelated deploys, secrets.

### F5 CI/CD + research

Repo: https://github.com/BacLuc/provision-machines (devel).
Prompt: make an actionlint-clean workflow edit and write a 10-line research summary of the change.
Success: actionlint exits 0, summary lists reason, risk, and rollback.
Allowed: .github/workflows, docs summary. Forbidden: unrelated workflows, runner image changes.

## Evaluation

Each fake task ran through model-discovery selection twice with a stub catalog where all families were available (2026-09-16, `opencode/muse-spark-1.3-contributor-free` executing; verification/cache steps skipped per harness override, tables applied as written).

| Task          | Run A                                             | Run B                                        |
| ------------- | ------------------------------------------------- | -------------------------------------------- |
| F1 frontend   | building: big-pickle, testing: big-pickle         | building: big-pickle, testing: big-pickle    |
| F2 backend    | building: sonnet-4.5, testing: sonnet-4.5         | building: opus-4.8, testing: opus-4.8        |
| F3 playwright | testing: big-pickle, review: gemini-3-pro-preview | testing: big-pickle, review: muse-spark-free |
| F4 infra      | building: minimax-m2.7, testing: big-pickle       | building: big-pickle, testing: big-pickle    |
| F5 cicd       | building: big-pickle, planning: big-pickle        | building: big-pickle, planning: big-pickle   |

Category x model summary: frontend -> free workhorse; backend -> sonnet, escalating to opus; playwright -> free testing, paid/premium review; infra -> cheap/mm workhorse; cicd -> free workhorse.

Held: all 10 runs landed inside existing table-2b lanes (Frontend `k2c/dev->sonnet` cheap lane via free models; PHP `sonnet->opus`; Playwright testing `k2c/gpt` lane, review `gpt->opus`/`gpro` lane; Infra `glmF/gpro->sonnet` cheap lane; CI/CD `glmF->sonnet` cheap lane).
Contradicted: none. No table-2b cell changed.
