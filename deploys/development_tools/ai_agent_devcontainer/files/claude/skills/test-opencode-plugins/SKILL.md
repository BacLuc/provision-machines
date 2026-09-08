---
name: test-opencode-plugins
description: Test opencode plugins end-to-end by starting an opencode session with the plugin activated and running specially crafted prompts.
---

# Testing opencode plugins end-to-end

## Why end-to-end tests

Plugin unit tests are not enough. A plugin can pass its unit tests and still fail in a real opencode session — wrong hook wiring, missing config keys, events that never fire. Always verify a plugin by starting an actual opencode session with the plugin activated and running specially crafted prompts that exercise the plugin's behavior.

## Start an opencode session with a specific plugin activated

Use an isolated config so the session only loads the plugin under test (and nothing from your real config):

```bash
# isolated config home
mkdir -p /tmp/opencode-plugin-test
XDG_CONFIG_HOME=/tmp/opencode-plugin-test opencode --command "<slash-command>" "<prompt>"
```

- `XDG_CONFIG_HOME` points opencode at a clean config directory where the plugin is registered
- `--command` executes a slash-command (e.g. `/my-plugin-command`) non-interactively and exits
- Add `--print-logs` or inspect the JSONL event output to see what the plugin did

## Inspect the JSONL event output

opencode writes every session event to a JSONL file. Find it under the isolated config home:

```bash
ls /tmp/opencode-plugin-test/opencode/log/
```

Each line is a JSON event. Grep for the plugin's events to confirm it ran:

```bash
grep -i "<plugin-name>" /tmp/opencode-plugin-test/opencode/log/*.jsonl
```

## Run specially crafted prompts

Craft prompts that trigger the exact code path the plugin implements:

- If the plugin reacts to a slash-command, invoke it via `--command`
- If the plugin reacts to certain content, include that content in the prompt
- If the plugin hooks lifecycle events (session start, tool call, message), make the prompt perform the corresponding action

Example:

```bash
XDG_CONFIG_HOME=/tmp/opencode-plugin-test opencode --command /my-plugin-command "run the plugin against this input"
```

## Verify the result

- The plugin's expected side effect happened (file written, tool called, message emitted)
- The JSONL log contains the plugin's events
- No errors in the session output

## When to use

This skill loads when developing or modifying opencode plugins or changing opencode config.
