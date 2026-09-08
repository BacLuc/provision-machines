---
name: test-ecamp3-pr-deployment
description: Test ecamp3 PR deployments by finding the deployment URL in the PR, using playwright-cli to test interactions, and capturing screenshots for comparison.
---

# Testing ecamp3 PR deployments

## Find the deployment URL

Go to the PR and find the "Feature branch deployment ready!" comment (tagged `feature-branch-deployment-status`). It shows the deployment URL:

```
https://pr<PR_NUMBER>.ecamp3.ch/
```

## Handle fallbacks

- **Deployment in progress:** the comment says the deployment is still building — wait and re-check
- **Deployment failed:** the comment reports the failure — investigate the deployment logs
- **No comment at all:** the PR needs the `deploy!` label to trigger a deployment -> you can stop, there is nothing to test.

## Login

Use the magic button to login with the test user.

## End-to-end testing with playwright-cli

Navigate to the changed components and test their interactions on desktop:

```bash
playwright-cli open https://pr<PR_NUMBER>.ecamp3.ch/
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

## Screenshots for comparison

Take screenshots on the devel deployment and on the PR deployment, then attach them to the PR:

```bash
playwright-cli screenshot --filename=devel.png
# ... same flow on the PR deployment ...
playwright-cli screenshot --filename=pr.png
gh pr comment <N> --attach devel.png
gh pr comment <N> --attach pr.png
```

- Devel deployment: `https://dev.ecamp3.ch/`
- PR deployment: `https://pr<PR_NUMBER>.ecamp3.ch/`

## When to use

This skill loads when testing ecamp3 PR deployments.
