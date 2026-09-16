---
name: github-fork-invite
description: Invite configured GitHub user on fork creation
allowed-tools: Bash(gh:*)
---

# GitHub Fork Invite

After any `gh repo fork`, invite the user in `$GITHUB_FORK_INVITE_USER` as a collaborator with `push` permission on the new fork. Runners wire this env var from the `FORK_INVITE_USER` repository variable or secret.

## Skip when unconfigured

```bash
if [ -z "${GITHUB_FORK_INVITE_USER:-}" ]; then
  echo "fork-invite: skip (GITHUB_FORK_INVITE_USER unset)"
  exit 0
fi
```

## Invite

Resolve the fork as `OWNER/REPO`, then check idempotency and invite:

```bash
FORK="bacluc-agent/<repo>"
USER="$GITHUB_FORK_INVITE_USER"
if ! gh api "repos/${FORK}/collaborators/${USER}" --silent; then
  gh api --method PUT "repos/${FORK}/collaborators/${USER}" -f permission=push || echo "fork-invite: warning: invite failed for ${USER} on ${FORK}, continuing"
fi
```

Use `push`, not `admin`. Never fail the parent task on invite errors: log a warning and continue.
