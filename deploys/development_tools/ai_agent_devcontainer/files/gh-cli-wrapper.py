#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from pathlib import Path


def deny(reason):
    raise ValueError(reason)


def owned_repo(repo):
    repo = re.sub(r"^(https://)?github\.com/", "", repo, flags=re.IGNORECASE)
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repo):
        deny("use an explicit github.com OWNER/REPO")
    owner, name = repo.split("/")
    if owner.lower() not in {"bacluc", "bacluc-agent"} or name in {".", ".."}:
        deny("create the PR in the bacluc-agent fork, not the upstream repository")


def options(args, values, switches):
    positional, parsed = [], {}
    index = 0
    while index < len(args):
        arg = args[index]
        index += 1
        if not arg.startswith("-"):
            positional.append(arg)
            continue
        key, separator, value = arg.partition("=")
        if arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
            key, separator, value = arg[:2], "=", arg[2:].removeprefix("=")
        if key in values:
            if not separator:
                if index == len(args):
                    deny(f"missing value for {key}")
                value = args[index]
                index += 1
            parsed.setdefault(values[key], []).append(value)
        elif key in switches and (not separator or value in {"true", "false"}):
            continue
        else:
            deny(f"unsupported or ambiguous option {key}")
    return positional, parsed


def validate_pr(args):
    prefix = []
    while args and (args[0] in {"-R", "--repo"} or args[0].startswith(("-R", "--repo="))):
        flag, *args = args
        prefix.append(flag)
        if flag in {"-R", "--repo"}:
            if not args:
                deny("missing repository")
            value, *args = args
            prefix.append(value)
    if not args or args[0].startswith("-"):
        deny("use gh pr SUBCOMMAND followed by options")
    if args[0] not in {"create", "new"}:
        return
    values = dict.fromkeys(("-R", "--repo"), "repo")
    values.update({key: key for key in ("-B", "--base", "-b", "--body", "-F", "--body-file", "-H", "--head", "-t", "--title")})
    positional, parsed = options(prefix + args[1:], values, {"-d", "--draft", "--dry-run", "--help"})
    if positional or len(parsed.get("repo", [])) != 1:
        deny("PR creation requires exactly one explicit -R/--repo destination")
    owned_repo(parsed["repo"][0])


def validate_api(args):
    values = {key: key for key in ("--jq", "-p", "--preview", "-t", "--template")}
    for name, flags in {"method": ("-X", "--method"), "host": ("--hostname",), "body": ("-f", "--raw-field", "-F", "--field", "--input"), "header": ("-H", "--header")}.items():
        values.update(dict.fromkeys(flags, name))
    positional, parsed = options(args, values, {"-i", "--include", "--paginate", "--silent", "--slurp", "--help"})
    if len(positional) != 1:
        deny("API calls require one unambiguous endpoint")
    if parsed.get("host", ["github.com"])[0].lower() != "github.com":
        deny("only github.com is supported")
    endpoint = positional[0].removeprefix("https://api.github.com/").lstrip("/")
    path = endpoint.partition("?")[0].rstrip("/")
    if path.lower() == "graphql":
        deny("direct GraphQL is disabled; use REST instead")
    if not re.fullmatch(r"[A-Za-z0-9_.{}-]+(?:/[A-Za-z0-9_.{}-]+)*", path):
        deny("use a canonical github.com REST path")


def main():
    backend = Path(__file__).resolve().with_name("real-gh").read_text().strip()
    args = sys.argv[1:]
    if not args or args[0] not in {"api", "auth", "issue", "label", "pr", "repo", "run", "search", "workflow", "version", "--version", "--help"}:
        deny("only builtin commands are supported")
    aliases = subprocess.run([backend, "alias", "list"], capture_output=True, text=True)
    if aliases.returncode:
        deny("cannot check configured gh aliases")
    if any(line.split(":", 1)[0].strip() == args[0] for line in aliases.stdout.splitlines()):
        deny("configured alias execution is disabled")
    if os.environ.get("GH_HOST", "github.com").lower() != "github.com":
        deny("only github.com is supported")
    if args[0] == "pr":
        validate_pr(args[1:])
    elif args[0] == "api":
        validate_api(args[1:])
    os.execv(backend, [backend, *args])


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"gh cli wrapper: {error}", file=sys.stderr)
        sys.exit(1)
