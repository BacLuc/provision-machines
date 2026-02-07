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
