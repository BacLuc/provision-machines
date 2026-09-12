---
description: Fake-task evaluation for model-discovery research (issue #142)
mode: all
hidden: true
temperature: 0.1
permission:
  "*": allow
---

# Model Discovery Research — Fake Tasks (Step 4)

Each fake task targets a different public repo and a different major category from step 1. Each is self-contained with an explicit success criterion.

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

## Task 5 — CI/CD and GitHub Actions automation / ecamp/ecamp3

**Repo:** https://github.com/ecamp/ecamp3
**Category:** CI/CD and GitHub Actions automation
**Prompt:**
> Add explicit minimal `permissions` blocks to the e2e workflow files (see ecamp/ecamp3#10720). Modify `.github/workflows/e2e.yml` (or the closest workflow file) to include `permissions: contents: read` and `pull-requests: write` at the workflow level. After editing, validate the YAML syntax with `python -c "import yaml; yaml.safe_load(open('.github/workflows/e2e.yml'))"` and confirm it parses cleanly.

**Success criterion:** A workflow YAML file that passes syntax validation (`yaml.safe_load` exits 0) and contains the required permissions block.

---

## Task 6 — Dependency management (renovate) / ecamp/ecamp3

**Repo:** https://github.com/ecamp/ecamp3
**Category:** Dependency management (renovate)
**Prompt:**
> Fix the renovate package lookup failure for a PHP dependency (see agent-todo#146 / ecamp/ecamp3 renovate PRs). Inspect the `renovate.json` or `package.json` / `composer.json` config and identify why a specific dependency update is failing. Write a one-line fix (e.g., add a regex override or update the datasource). After editing, verify the config parses (`python -c "import json; json.load(open('renovate.json'))"`) and the fix addresses the lookup failure.

**Success criterion:** A config file that passes parser validation (`json.load` exits 0) and contains the fix.

---

## Task 7 — Research / Planning / bacluc-agent/agent-todo

**Repo:** https://github.com/bacluc-agent/agent-todo
**Category:** Research / Planning
**Prompt:**
> Analyze the reasons for flaky e2e tests in ecamp/ecamp3 (see agent-todo#172). Read the issue description and any linked PRs or comments. Produce a structured analysis document (`research/flaky-e2e-analysis.md`) with: (1) observed failure patterns, (2) suspected root causes, (3) proposed fixes ranked by effort. The document must be at least 200 words and cite specific issue/PR numbers.

**Success criterion:** A research document (`research/flaky-e2e-analysis.md`) that exists, is at least 200 words, and cites specific issue/PR numbers.
