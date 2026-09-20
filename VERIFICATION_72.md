# Standing Task Verification: bacluc-agent/agent-todo#72

Run: 2026-09-20
Branch: issue-72-verify-sha

## Open Renovate PRs checked

- bacluc/provision-machines#182 (renovate/alpine-3.x) — alpine 3.24.2 + aichat v0.30.0
  - AICHAT_CHECKSUM verified: 6b0cc08c5ceb551dc52bfac2221752f82215be5908c70605d655e9b91ab1557c (musl binary)
- bacluc/provision-machines#145 (renovate/ghcr.io-open-webui-open-webui-0.x) — docker tag, no checksum
- bacluc/provision-machines#121 (renovate/opencode-ai-1.x) — npm version, no checksum
- bacluc/provision-machines#120 (renovate/openai-codex-0.x) — npm version, no checksum
- bacluc/provision-machines#119 (renovate/anthropic-ai-claude-code-2.x) — npm version, no checksum
- bacluc/provision-machines#117 (renovate/ruff-0.x) — python package, no checksum
- bacluc/provision-machines#116 (renovate/mypy-2.x) — python package, no checksum
- bacluc/provision-machines#115 (renovate/t3-0.x) — npm version, no checksum
- bacluc/provision-machines#100 (renovate/ollama-ollama-0.x) — version bump, no checksum variable
- bacluc/provision-machines#68 (renovate/php-php-src-8.x) — version bump, no checksum variable

## Related PRs verified

- bacluc/provision-machines#186 (issue-72-sha-update) — checksums verified correct
- bacluc/provision-machines#185 (issue-72-fix-sha-aichat-v030) — AICHAT_CHECKSUM verified correct

## Verification commands

```bash
curl -sL https://github.com/sigoden/aichat/releases/download/v0.30.0/aichat-v0.30.0-x86_64-unknown-linux-musl.tar.gz | sha256sum
# => 6b0cc08c5ceb551dc52bfac2221752f82215be5908c70605d655e9b91ab1557c

curl -sL https://releases.astral.sh/github/uv/releases/download/0.12.10/uv-x86_64-unknown-linux-musl.tar.gz | sha256sum
# => 848d0e261119e5b8f35db10164635e46a48bec29ceb1f8ec14a6fc76004973ee
```

Result: No Renovate PR currently requires a SHA fix. All paired checksums match real binary sha256 values.
