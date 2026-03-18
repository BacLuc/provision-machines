# This file contains different issues that can be fixed in this repo

Each issue is in a h2 block.
Use subagents to solve the issues one by one. If one subagent gets stuck, stop it and start another one.
Do not stop. If an issue is too hard, skip it and try it later.
If an issue is fixed, mark it with the text fixed.
First, read the AGENTS.md, and then start fixing issues.
Make commits for each individual changes and make small commits with messages consistent with the previous commits.
All roles must run, dependency updates must work and formatter and linter must run for all commits.
Use the review agent to review your changes, and run all roles you changed to test if they still work.

## add role ai_agent_devcontainer

create me a new role ai_agent_devcontainer.
It creates a script in home/bin directory which starts a devcontainer in the current directory. But the devcontainer config is not used of the current working directory, it is used from a central
location in this repository.
Use the universal image that many tools are already installed. then install opencode as already defined in [text](.devcontainer/ansible/Dockerfile)
2 opencode json must be mounted into the container: one if the provider configuration and their models, and one with the api keys.
also: a directory with the agent descriptions from the host must be mounted into /home/vscode/.config/opencode/agents.

It then starts opencode in the webui mode that it can be used from the host browser.

