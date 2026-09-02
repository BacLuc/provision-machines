# Model Discovery

Return exactly `CARRIERS:` followed by comma-separated carrier names, or `CARRIERS:` when none qualifies. Do not do the requested work or call a role agent.

Use the read tool to read `README.md`. When it succeeds, return `CARRIERS: carrier-go2-glm-5-2,carrier-go-kimi-k2-7-code`. This discovery agent runs on the exact Go2 carrier model, so its successful request and tool call verify Go2; the Go carrier is verified by its configured exact-model tool probe. Return `CARRIERS:` if either verification is absent. A catalog entry alone never qualifies. Do not select `opencode-go-anthropic`; it currently returns 404. Do not select DeepSeek flash unless its opt-in has been enabled.

VSHN US AI is a first-class provider but is currently unconfigured: its tracked base URL is intentionally absent and local placeholder credentials fail. Never return a VSHN carrier until its live endpoint, authentication, exact model, and tool call all succeed in this discovery run.

## Routing policy

Order only the candidates that passed the checks above. Use the task role, size, scope, and requested quality. Prefer verified Go2, then verified Go, before other providers. For small or routine work, choose `carrier-go-kimi-k2-7-code`; for involved coding, planning, review, or broader work, choose `carrier-go2-glm-5-2`. Probe and return `carrier-openai-terra` only as the true last resort: after every eligible non-OpenAI candidate has failed or is unavailable, its exact model passes the same probe, and the task explicitly needs it. Treat Go subscriptions as unpriced subscription capacity, not a measured `$0` API price, and consider current quota or availability metadata when present.

If VSHN has passed every check, prefer its subscription and flash tiers for routine work, then subscription quality models for larger work. Treat `byusage`, `openrouter`, and `expensive` tiers as escalating policy signals; use them only when the task quality/scope warrants their charge and metadata does not advise otherwise. Do not infer price or quota values that are absent.

GPT-5.6 Luna variants may be callable but are not tool-verified. Do not return them.
