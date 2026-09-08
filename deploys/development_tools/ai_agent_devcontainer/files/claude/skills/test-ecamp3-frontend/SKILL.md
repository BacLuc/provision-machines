---
name: test-ecamp3-frontend
description: Test the ecamp3 frontend (Vue.js with Vite) by running unit tests, using playwright-cli for end-to-end testing, and capturing screenshots for PR comparison.
---

# Testing the ecamp3 frontend

## Where the frontend lives

The ecamp3 frontend is in the `ecamp/ecamp3` repository under `frontend/`. It is a Vue.js 3 application built with Vite and Vuetify.

## Unit tests

Run from the `frontend/` directory:

```bash
cd frontend
npm run test:unit
```

This runs vitest with coverage.

## Start the whole stack

From the repo root:

```bash
docker compose up -d
./wait-for-container-startup.sh
```

## Login

Use the test account:

- User: `test@example.com`
- Password: `test`

## End-to-end testing with playwright-cli

Navigate to the changed components and test their interactions on desktop:

```bash
playwright-cli open https://dev.ecamp3.ch/
playwright-cli snapshot
playwright-cli click e15
playwright-cli snapshot
```

## Mobile

Repeat the same flow at mobile viewport size:

```bash
playwright-cli resize 390 844
playwright-cli snapshot
playwright-cli click e15
playwright-cli snapshot
```

## Screenshots for PR comparison

Take screenshots on the devel deployment and on the branch deployment, then attach them to the PR:

```bash
playwright-cli screenshot --filename=devel.png
# ... same flow on the branch deployment ...
playwright-cli screenshot --filename=branch.png
gh pr comment <N> --attach devel.png
gh pr comment <N> --attach branch.png
```

- Devel deployment: `https://dev.ecamp3.ch/`
- Branch deployment: `https://pr<NUMBER>.ecamp3.ch/`

## Notes

- The default branch of `ecamp/ecamp3` is `devel`

## When to use

This skill loads when developing or testing the ecamp3 frontend.