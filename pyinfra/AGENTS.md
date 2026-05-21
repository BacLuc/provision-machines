# Provision machines

This is an pyinfra deploy to provision development machines.
All features are split up into deploys as good as possible.
Dependencies are expressed with python imports of the depending deploy.

Colocation is preferred to separating all templates out of the main script.

You are running in a development container, you only brick the container if your code is wrong.
You must test the scripts, the systemctl service files and the deploy you write.
Do not stop until all use cases are tested.

uv and pyinfra are already installed.
If you need another tool, set it up with pyinfra and install it with pyinfra.

Use the following command to run the pyinfra deploy:

```shell
uv run scripts/run_pyinfra_local.py
```

It may be that not everything works because you are in a container.
Also read the README.md.

## Renovate

Renovate must be able to update all dependencies.
For that we use a regex pattern where we have the renovate instructions in a comment above.
