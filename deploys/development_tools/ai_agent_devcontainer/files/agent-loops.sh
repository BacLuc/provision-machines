#!/bin/bash

set -euo pipefail

AGENT_LOOPS_ROOT="${AGENT_LOOPS_ROOT:-$HOME/projects/agent-runner}"
exec npm exec --prefix "$AGENT_LOOPS_ROOT" --workspace @bacluc-agent/agent-loops -- agent-loops \
  --repository "${AGENT_LOOPS_REPOSITORY:-$(git -C "$PWD" remote get-url origin | sed -E 's#^https://github.com/##; s#\.git$##')}" \
  --issue-repository "${ISSUE_REPOSITORY:-bacluc-agent/agent-todo}" \
  --repeat --phases refine,hourly,review "$@"
