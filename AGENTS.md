# Provision machines

This is an ansible playbook to provision development machines.
All features are split up into roles as good as possible.
Dependencies are expressed with meta/main.yml, not with role imports.

Include_role are used when a role instance is used with different parameters, like in
roles/kubectl/main.yml the include_role of github_release_binary.

Colocation is preferred to seperating all templates out of the main script.
ansible.builtin.copy with src is more readable.

You are running in a development container, you only brick the container if your ansible is wrong.
You must test the scripts, the systemctl service files and the ansible roles you write.
Do not stop until all use cases are tested.

Use the following command to run the ansible roles:

```
ansible-playbook -e "ansible_python_interpreter=python" --connection=local playbook.yml --inventory inventory/local.yaml -t nvm
```

It may be that not everything works because you are in a container.

Every commit has to pass:
docker compose run --rm prettier && docker compose run --rm ansible-lint && docker compose run --rm yamllint.

## Renovate

Renovate must be able to update all dependencies.
For that we use a regex pattern where we have the renovate instructions in a comment above, and all versions
are in a single variable in the ansible task file.

```json
{
  "customType": "regex",
  "managerFilePatterns": ["/^.*.ya?ml/"],
  "matchStrings": [
    "renovate: datasource=(?<datasource>.*?) depName=(?<depName>.*?)?\\s.*tag: \"(?<currentValue>.*)\"\\s"
  ]
}
```

```yaml
# renovate: datasource=docker depName=node
tag: "24.13.0"

ollama_defaults:
  # renovate: datasource=github-releases depName=ollama/ollama
  ollama_version: "0.15.2"
```

use `./scripts/update-renovate-snapshot.sh` to check if the dependency can be extracted,
and update the snapshot if you changed something where a dependency is used, or if you changed renovate.json.
