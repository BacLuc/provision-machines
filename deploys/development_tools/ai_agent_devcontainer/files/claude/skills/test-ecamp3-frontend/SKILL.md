---
name: test-ecamp3-frontend
description: Test the ecamp3 frontend (Vue.js with Vite) by running unit tests, using playwright-cli for end-to-end testing, and capturing screenshots for PR comparison.
---

# Testing the ecamp3 frontend

## Start the whole stack

From the repo root:

```bash
docker compose up -d
./wait-for-container-startup.sh
```

## Login

You can use the magic button to login with the test user.

## End-to-end testing with playwright-cli

Navigate to the changed components and test their interactions on desktop:

```bash
playwright-cli open http://localhost:3000
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

Take screenshots on the devel deployment and on localhost, then attach them to the issue or PR:

```bash
playwright-cli screenshot --filename=devel.png
# ... same flow on the branch deployment ...
playwright-cli screenshot --filename=branch.png
gh pr comment <N> --attach devel.png
gh pr comment <N> --attach branch.png
```

- Devel deployment: `https://dev.ecamp3.ch/`
- Local deployment: `http://localhost:3000`

## When to use

This skill loads when developing or testing the ecamp3 frontend.
