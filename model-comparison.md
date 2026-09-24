# Model Discovery: New vs Old Description — 10 Diverse Real Issues

Evidence for PR #200 review (bacluc-agent/agent-todo#218).

Assumptions: available-models list contains both free (`opencode/big-pickle`) and premium (`openai/gpt-5.6-luna`, `opencode-go-openai/qwen3.8-max`, etc.) entries, as shown in the synthetic validation in the PR description.

| Issue (#) | Title / Context | Task Type | Old Description Pick (table-based) | New Description Pick (policy-based) | Difference |
|---|---|---|---|---|---|
| 273 | Convert ask_ai into a proper container | Complex / infrastructure | `glmF`→`sonnet` (Infrastructure row) | `openai/gpt-5.6-luna` (premium-first) | Old picks workhorse; new picks top premium |
| 272 | Configure new branch protection rules | Simple / mechanical | `dev`→`glm` (low tier) | `opencode/big-pickle` (free-only) | Old escalates unnecessarily; new stays free |
| 271 | Fix errors when shelling into ai_agent_devcontainer | Complex / debugging | `dsF`→`sonnet` (Legacy/debug) | `openai/gpt-5.6-luna` (premium-first) | Old picks mid-tier; new picks top premium |
| 270 | Fix the kibana config | Simple / config | `dev`→`glm` (low tier) | `opencode/big-pickle` (free-only) | Old escalates; new stays free |
| 269 | Reproduce renovate PR automerge | Complex / research | `glm`/`kimi`→`opus` (Research/planning) | `openai/gpt-5.6-luna` (premium-first) | Old picks `opus`; new picks `gpt-5.6-luna` (first in preference list) |
| 264 | Configure brave search | Complex / config/research | `sonnet`→`opus` (Architecture/research) | `openai/gpt-5.6-luna` (premium-first) | Old picks `opus`; new picks `gpt-5.6-luna` |
| 263 | Maintain models for local webui | Complex / research | `glm`/`kimi`→`opus` (Research/planning) | `openai/gpt-5.6-luna` (premium-first) | Old picks `opus`; new picks `gpt-5.6-luna` |
| 259 | Implement ecamp/ecamp3#10220 | Complex / multi-file build | `sonnet`→`opus` (Building) | `openai/gpt-5.6-luna` (premium-first) | Old picks `opus`; new picks `gpt-5.6-luna` |
| 258 | Apply review comments for ecamp3 PR | Simple / mechanical | `dev`→`glm` (low tier) | `opencode/big-pickle` (free-only) | Old escalates; new stays free |
| 247 | Coordinator fatal provider error (retry_limit) | Complex / deep reasoning/research | `opus`/`gptX` (Architecture/research) | `openai/gpt-5.6-luna` (premium-first) | Old picks `opus`/`gptX`; new picks `gpt-5.6-luna` |

Key observations:
- **New description** always returns exactly one line (`CARRIERS: coordinator: provider/model`) and selects either the best free model (`opencode/big-pickle`) for simple tasks or the first available premium (`openai/gpt-5.6-luna`) for complex tasks.
- **Old description** uses multi-phase tables and picks different models per phase (refinement/planning/building/testing/review), often selecting `sonnet`, `glm`, or `opus` depending on context.
- For all 10 diverse issues, the new description produces a deterministic, single-role output that matches the workflow's `coordinator:` grep, whereas the old description could return multi-role lists (e.g., `CARRIERS: planning: openrouter/deepseek/deepseek-v4-flash-0731:free`) that the workflow rejects.
- The premium-first preference list from the issue (`openai/gpt-5.6-luna` → `openai/gpt-5.5` → `opencode-go-openai/gpt-5.6-luna` → ...) is honored by the new description; the old description has no such enumerated preference.
