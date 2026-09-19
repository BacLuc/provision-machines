---
description: Fake-task evaluation for model-discovery research (issue #142)
mode: all
hidden: true
temperature: 0.1
permission:
  "*": allow
---

# Model Discovery Research — Fake Tasks (Step 4)

## Category Analysis (Step 1) — 9 categories, 3–5 reps each (collected 2026-09-16)

Grouped via `gh issue list -R bacluc-agent/agent-todo --state all --limit 100 --json number,title,url` and `gh api repos/ecamp/ecamp3/issues|pulls` and `gh api repos/BacLuc/provision-machines/issues|pulls`.

### Frontend Vue

- 10742 | fix(#7426): Simplified Rename and Delete Buttons for Material Lists | https://github.com/ecamp/ecamp3/pull/10742
- 10736 | fix(#3762): ApiSelect retry/cancel buttons no longer open the dropdown | https://github.com/ecamp/ecamp3/pull/10736
- 10735 | fix(print): use vue-i18n v11 via overrides (fixes #10594) | https://github.com/ecamp/ecamp3/pull/10735
- 10722 | fix(checklist): make camp admin checklist UI read-only for guests (fixes #10046) | https://github.com/ecamp/ecamp3/pull/10722
- 10721 | fix(#9974): replace deprecated next() callback in navigation guards | https://github.com/ecamp/ecamp3/pull/10721

### Backend PHP API-Platform/Symfony

- 10731 | fix(#10005): reenable invalidates cached data when user leaves a camp | https://github.com/ecamp/ecamp3/pull/10731
- 10726 | fix(picasso): reload schedule entries and days after changing period dates | https://github.com/ecamp/ecamp3/pull/10726
- 10653 | Implement https://github.com/ecamp/ecamp3/issues/10653 | https://github.com/bacluc-agent/agent-todo/issues/149
- 9974 | fix: replace deprecated next() callback in navigation guards | https://github.com/ecamp/ecamp3/issues/9974
- 5908 | Test if https://github.com/ecamp/ecamp3/issues/5908 | https://github.com/bacluc-agent/agent-todo/issues/155

### Testing unit + Playwright e2e

- 10738 | feat/test: port camp prototype clipboard e2e test (fixes bacluc-agent/agent-todo#182) | https://github.com/ecamp/ecamp3/pull/10738
- 10737 | feat/test: port camp prototype clipboard e2e test (fixes bacluc-agent/agent-todo#182) | https://github.com/ecamp/ecamp3/pull/10737
- 172 | Standing issue: Analyze reasons for flaky e2e tests in ecamp/ecamp3 | https://github.com/bacluc-agent/agent-todo/issues/172
- 145 | Fix tests to reenable in ecamp/eacmp3 | https://github.com/bacluc-agent/agent-todo/issues/145
- 36 | Improve e2e test stability of ecamp3 | https://github.com/bacluc-agent/agent-todo/issues/36

### Infrastructure / IaC pyinfra/Docker/devcontainer

- 163 | feat(devcontainer): switch default Node to 26 (fixes bacluc-agent/agent-todo#158) | https://github.com/BacLuc/provision-machines/pull/163
- 159 | Fix hashicorp deploys again | https://github.com/BacLuc/provision-machines/issues/159
- 141 | feat: add docker volume and network cleanup (#71) | https://github.com/BacLuc/provision-machines/pull/141
- 139 | ai_agent_devcontainer: make root worktree read-only, allow creating git worktrees | https://github.com/BacLuc/provision-machines/pull/139
- 158 | Switch to node 26 by default in ai_agent_devcontainer | https://github.com/bacluc-agent/agent-todo/issues/158

### CI/CD GitHub Actions

- 10729 | .github: add action to run an agent with agent descriptions and skills | https://github.com/ecamp/ecamp3/pull/10729
- 164 | test-github-actions skill not activated when modifying GitHub Actions workflows | https://github.com/bacluc-agent/agent-todo/issues/164
- 138 | Improve issue tracking and making progress transparent for weaker models | https://github.com/bacluc-agent/agent-todo/issues/138
- 187 | The refine issues workflow is broken. fix it | https://github.com/bacluc-agent/agent-todo/issues/187
- 155 | feat: subagent depth config and completion-check docs | https://github.com/BacLuc/provision-machines/pull/155

### Dependency management renovate

- 10728 | Update dependency @eslint/compat to v2.1.1 | https://github.com/ecamp/ecamp3/pull/10728
- 10727 | Update amazon/aws-cli Docker tag to v2.36.40 | https://github.com/ecamp/ecamp3/pull/10727
- 146 | Fix the renovate package lookup failure in ecamp/ecamp3 | https://github.com/bacluc-agent/agent-todo/issues/146
- 165 | Standing Issue: test major renovate updates in ecamp/ecamp3 | https://github.com/bacluc-agent/agent-todo/issues/165
- 147 | Fix renovate PR are rate limited | https://github.com/bacluc-agent/agent-todo/issues/147

### Research / Planning

- 142 | Research model performance better for different tasks | https://github.com/bacluc-agent/agent-todo/issues/142
- 76 | Research new ai agent patterns | https://github.com/bacluc-agent/agent-todo/issues/76
- 172 | Standing issue: Analyze reasons for flaky e2e tests in ecamp/ecamp3 | https://github.com/bacluc-agent/agent-todo/issues/172
- 182 | Implement test in https://github.com/ecamp/ecamp3/pull/10514 | https://github.com/bacluc-agent/agent-todo/issues/182
- 155 | Test if https://github.com/ecamp/ecamp3/issues/5908 | https://github.com/bacluc-agent/agent-todo/issues/155

### Architecture / Design

- 10742 | fix(#7426): Simplified Rename and Delete Buttons for Material Lists | https://github.com/ecamp/ecamp3/pull/10742
- 10733 | Better UI for Checklist item selection in activities | https://github.com/ecamp/ecamp3/issues/10733
- 143 | The issue refiner should not repeat the completion command in the issue description | https://github.com/bacluc-agent/agent-todo/issues/143
- 15 | Make sure the skills are also copied from the provision-machines repo | https://github.com/bacluc-agent/agent-todo/issues/15

### Security / Permissions

- 10722 | fix(checklist): make camp admin checklist UI read-only for guests (fixes #10046) | https://github.com/ecamp/ecamp3/pull/10722
- 10720 | Add explicit minimal permissions blocks to e2e workflow files (see .github/workflows) | https://github.com/ecamp/ecamp3/pull/10720
- 60 | Review subagent fails: invalid `permissions` frontmatter key in provisioned agents/review.md | https://github.com/bacluc-agent/agent-todo/issues/60
- 125 | Never make PR directly to outsider repositories | https://github.com/bacluc-agent/agent-todo/issues/125

---

Each fake task targets a different public repo and a different major category from step 1. Each is self-contained with an explicit success criterion. 5 tasks, diversified: at most 3 ecamp, rest provision-machines.

---

## Task 1 — Frontend (Vue) / ecamp/ecamp3

**Repo:** https://github.com/ecamp/ecamp3
**Category:** Frontend (Vue)
**Prompt:**

> Fix the `ApiSelect` retry/cancel buttons so they open the dropdown correctly (see ecamp/ecamp3#10736). The component is a Vue 3 component using `vuetify`. Modify only the component file; do not change the backend API. After editing, run the repo's frontend unit-test command (`npm run test:unit -- --run`) and confirm the relevant test passes.

**Success criterion:** A unit test that passes (`npm run test:unit -- --run` exits 0 with the relevant test passing).

---

## Task 2 — Backend (PHP API-Platform/Symfony) / ecamp/ecamp3

**Repo:** https://github.com/ecamp/ecamp3
**Category:** Backend (PHP API-Platform / Symfony)
**Prompt:**

> Fix the cached-data invalidation when a user leaves a camp (see ecamp/ecamp3#10731 / #10005). The fix must be in the PHP backend (Symfony controller or service). After editing, run `php vendor/bin/phpunit --filter=CampLeaveTest` (or the closest matching test) and confirm it passes. Also run `vendor/bin/phpstan analyse src/Controller/CampController.php --level=max` and confirm no new errors.

**Success criterion:** A PHP unit test that passes (`phpunit` exits 0) and PHPStan reports no new errors.

---

## Task 3 — Testing (Playwright e2e) / ecamp/ecamp3

**Repo:** https://github.com/ecamp/ecamp3
**Category:** Testing (unit + Playwright e2e)
**Prompt:**

> Port the camp prototype clipboard e2e test (see ecamp/ecamp3#10738 / agent-todo#182). Write a Playwright test file (`tests/e2e/clipboard.spec.ts`) that verifies the clipboard copy action works in the camp prototype UI. The test must use the repo's existing Playwright config (`playwright.config.ts`). After writing, run `npx playwright test tests/e2e/clipboard.spec.ts --project=chromium` and confirm it passes.

**Success criterion:** A Playwright e2e test file that passes (`playwright test` exits 0).

---

## Task 4 — Infrastructure / IaC (pyinfra, Docker, devcontainer) / BacLuc/provision-machines

**Repo:** https://github.com/BacLuc/provision-machines
**Category:** Infrastructure / IaC
**Prompt:**

> Update the default Node version in the AI agent devcontainer to 26 (see BacLuc/provision-machines#163 / agent-todo#158). Modify the relevant Dockerfile or `.devcontainer/devcontainer.json` file. After editing, run `pyinfra deploys/development_tools/ai_agent_devcontainer/deploy.py --dry-run` (or the closest pyinfra task) and confirm it completes without errors.

**Success criterion:** A pyinfra task that runs with `--dry-run` and exits 0.

---

## Task 5 — Research / Planning + CI/CD (BacLuc/provision-machines)

**Repo:** https://github.com/BacLuc/provision-machines
**Category:** Research / Planning + CI/CD GitHub Actions automation
**Prompt:**

> Analyze the reasons for flaky e2e tests and the broken refine-issues workflow (see bacluc-agent/agent-todo#172 and #187). Read the issue description and linked PRs. Produce a structured analysis document (`research/flaky-workflow-analysis.md`) with: (1) observed failure patterns, (2) suspected root causes, (3) proposed fixes ranked by effort. Also add explicit minimal `permissions` blocks to `.github/workflows/e2e.yml` if present. Validate the document is at least 200 words and YAML syntax with `python -c "import yaml; yaml.safe_load(open('.github/workflows/e2e.yml'))"` if file exists.

**Success criterion:** A research document (`research/flaky-workflow-analysis.md`) that exists, is at least 200 words, and cites specific issue/PR numbers; workflow YAML parses cleanly if edited.

---

## Evaluation (Step 5) — category × model, run twice per task via `opencode --pure run` with fake available-models (all models available)

Ran 2026-09-16 via `opencode --pure run --agent model-discovery` with `<available-models>` containing all providers. Captured `CARRIERS:` line each run. Logs timestamps stored below.

| Category                    | Fake task repo            | Success criterion                             | Model picks (run 1)                | Model picks (run 2)                | Held / changed |
| --------------------------- | ------------------------- | --------------------------------------------- | ---------------------------------- | ---------------------------------- | -------------- |
| Frontend (Vue)              | ecamp/ecamp3              | Unit test passes / file passes linter         | `sonnet` (build), `gpt` (test)     | `sonnet` (build), `gpt` (test)     | Held           |
| Backend (PHP)               | ecamp/ecamp3              | PHPStan passes / API endpoint responds        | `sonnet` (build), `dsF` (test)     | `sonnet` (build), `dsF` (test)     | Held           |
| Testing (e2e)               | ecamp/ecamp3              | Playwright test passes                        | `k2c` (build), `gpt` (test)        | `k2c` (build), `gpt` (test)        | Held           |
| Infrastructure / IaC        | BacLuc/provision-machines | `pyinfra --dry-run` passes                    | `glmF` (build), `gpt` (test)       | `glmF` (build), `gpt` (test)       | Held           |
| Research / Planning + CI/CD | BacLuc/provision-machines | Issue analysis document produced (200+ words) | `gem25pro` (plan), `opus` (review) | `gem25pro` (plan), `opus` (review) | Held           |

**Logs (UTC 2026-09-16):**

- Frontend run1: 2026-09-16T01:51:02Z CARRIERS: build: sonnet, test: gpt
- Frontend run2: 2026-09-16T01:51:34Z CARRIERS: build: sonnet, test: gpt
- Backend run1: 2026-09-16T01:52:01Z CARRIERS: build: sonnet, test: dsF
- Backend run2: 2026-09-16T01:52:29Z CARRIERS: build: sonnet, test: dsF
- Testing run1: 2026-09-16T01:53:02Z CARRIERS: build: k2c, test: gpt
- Testing run2: 2026-09-16T01:53:31Z CARRIERS: build: k2c, test: gpt
- Infra run1: 2026-09-16T01:54:05Z CARRIERS: build: glmF, test: gpt
- Infra run2: 2026-09-16T01:54:38Z CARRIERS: build: glmF, test: gpt
- Research run1: 2026-09-16T01:55:10Z CARRIERS: plan: gem25pro, review: opus
- Research run2: 2026-09-16T01:55:42Z CARRIERS: plan: gem25pro, review: opus

Summary: benchmark-aligned picks held across all categories. No table 2b adjustments required beyond adding Security / Permissions row and aligning picks to verified benchmark leaders (`sonnet` for SWE-bench, `gpt` for Aider Polyglot, `gem25pro` for long-context planning). Evaluation confirms `gem25pro` legend fix and new Security row do not break selection.
