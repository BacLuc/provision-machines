# Provision machines

This is an pyinfra deploy to provision development machines.
All features are split up into deploys as good as possible.
Dependencies are expressed with

```python
local.include(f"{DEPLOYS_DIR}/docker/deploy.py")
```

for example.

Colocation is preferred to separating all templates out of the main script.

You are running in a development container, you only brick the container if your code is wrong.
You must test the scripts, the systemctl service files and the deploy you write.
Do not stop until all use cases are tested.

uv and pyinfra are already installed.
If you need another tool, set it up with pyinfra and install it with pyinfra.

NEVER NEVER use comments.

Use the following command to run the pyinfra deploy:

```shell
uv run scripts/run_pyinfra_local.py
```

It may be that not everything works because you are in a container.
Also read the README.md.

Keep the style of the imports and how the group vars accessed.
Also don't use unnecessary functions, keep the style as it was, simple and understandable.

## Renovate

Renovate must be able to update all dependencies.
For that we use a regex pattern where we have the renovate instructions in a comment above, and all versions
are assigned to a python variable or a dict entry, and have a renovate comment on top.

```json
{
  "fileMatch": [".*"],
  "matchStrings": [
    "# renovate: datasource=(?<datasource>[^\\s]+) depName=(?<depName>[^\\s]+)\\n\\s*[\"\\w][^:=\\n]*[:=]\\s*['\"]*(?<currentValue>v?[0-9][\\w.-]*)"
  ],
  "datasourceTemplate": "{{{datasource}}}"
}
```

```yaml
# renovate: datasource=github-releases depName=vshn/k8ify
k8ify_version = "2.5.0"
k8ify_checksum = "f3605d34439c0bef36930c71ad2b066acc0ba821e68c98e764fffc1a66dcc3b9"

# renovate: datasource=github-releases depName=jsonnet-bundler/jsonnet-bundler
jsonnet_bundler_version = "0.6.3"
jsonnet_bundler_checksum = "424be2836ffee389d93a8cb873eb891a69fef4509026c7c1a825943292b8c841"

```

use `./scripts/update-renovate-snapshot.sh` to check if the dependency can be extracted,
and update the snapshot if you changed something where a dependency is used, or if you changed renovate.json.
