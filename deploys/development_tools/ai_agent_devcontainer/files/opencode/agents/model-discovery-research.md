---
description: Fake evaluation tasks for model-discovery benchmark alignment
mode: all
hidden: true
temperature: 0.1
permission:
  "*": allow
---

# Fake Evaluation Tasks

## Task 1: CI/CD Workflow Fix (bacluc-agent/agent-todo)

- **Repo:** `bacluc-agent/agent-todo`
- **Category:** CI/CD + GitHub Actions
- **Task:** Fix broken `.github/workflows/refine-issues.yml` (issue #187 reference).
- **Success criterion:** Workflow passes `actionlint` and `gh workflow run` completes with exit 0; no permission errors.

## Task 2: Dependency Update (ecamp/ecamp3)

- **Repo:** `ecamp/ecamp3`
- **Category:** Dependency management (renovate)
- **Task:** Resolve renovate PR #10754 (update `justinrainbow/json-schema` to v6.12.0) and verify lock-file consistency.
- **Success criterion:** `composer install` passes; `renovate` PR merges without conflicts; `uv sync --frozen` clean.

## Task 3: Playwright E2E Flaky Test Fix (ecamp/ecamp3)

- **Repo:** `ecamp/ecamp3`
- **Category:** Testing (Playwright e2e)
- **Task:** Fix flaky login test (`can login with default user`) per PR #10747; add `expect(page).toHaveURL` instead of `waitForURL`.
- **Success criterion:** Test passes 5/5 consecutive runs; no `waitForURL` calls remain in file.

## Task 4: Security/Permissions Audit (BacLuc/provision-machines)

- **Repo:** `BacLuc/provision-machines`
- **Category:** Security/permissions
- **Task:** Review agent frontmatter `permissions` keys (issue #60 reference); ensure no `permissions` key errors in `agents/review.md`.
- **Success criterion:** `actionlint` passes; `permissions` key valid YAML; no PR restrictions violated.

## Task 5: Architecture/Design Planning (bacluc-agent/agent-todo)

- **Repo:** `bacluc-agent/agent-todo`
- **Category:** Research/planning
- **Task:** Design bounded evaluator loop for issue refinement (issue #120 reference); document phase contracts.
- **Success criterion:** Design doc saved; coordinator prompts split into plan/execute/verify phases; contracts validated.
