# This file contains different issues that can be fixed in this repo

Each issue is in a h2 block.
Use subagents to solve the issues one by one. If one subagent gets stuck, stop it and start another one.
Do not stop. If an issue is too hard, skip it and try it later.
If an issue is fixed, mark it with the text fixed.
First, read the AGENTS.md, and then start fixing issues.

## Add role with script to apply intellij vm settings to new versions of intellij - FIXED

Here is an idea for the script:

```
#!/bin/bash

# Define the target directory and the line to add
TARGET_DIR="$HOME/.config/JetBrains"
VM_OPTIONS_FILE="idea64.vmoptions"
LINE_TO_ADD="-Xmx8096m"

# Check if the directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Directory $TARGET_DIR does not exist."
  exit 1
fi

# Find all idea64.vmoptions files recursively
find "$TARGET_DIR" -name "$VM_OPTIONS_FILE" | while read -r vm_file; do
  # Check if the line already exists in the file
  if grep -qF -- "$LINE_TO_ADD" "$vm_file"; then
    echo "Skipping: $vm_file (Line already exists)"
  else
    echo "Updating: $vm_file"
    # Append the line to the end of the file
    echo "$LINE_TO_ADD" >> "$vm_file"
  fi
done

echo "Done."
```

This script can be run at startup with systemctl or by the user.
You can fake an empty idea64.vmoptions at the correct location

## Add a docker cleanup script - FIXED

docker system prune leaves way to many images.
I want you to create a script that goes through all the containers which have a size of > 200 MB
and checks their last usage.
If the last usage is > 2M, delete the image.
THe script should be added to the cleanup.d directory.
(see cleanup_scripts role and its dependendts).
The script should be provisioned in the docker role, the docker role should then depend on the cleanup_scripts role.

## Renovate this repo

Use regex managers to update the depenencies of this repo with the pattern:

```
operator:
  annotations:
    trigger-recreate: {{ exec "uuidgen" (list) }}
  container:
    # renovate: datasource=docker depName=ghcr.io/fluent/fluent-operator/fluent-operator
    tag: "v3.5.0"
```

the comment is parsed by the regex manager and used to find the dependency and the version part, and then updated with renovate.

you can find an example renovate.json here:
https://raw.githubusercontent.com/ecamp/ecamp3/refs/heads/devel/renovate.json

## Renovate this repo - FIXED ✅

### Complete Version Inventory (All git-tracked files)

| File                                                    | Line | Version Pattern | Current Value | Package/Tool                         | Type                 |
| ------------------------------------------------------- | ---- | --------------- | ------------- | ------------------------------------ | -------------------- |
| .devcontainer/ansible/Dockerfile                        | 1    | Docker image    | ubuntu-24.04  | mcr.microsoft.com/devcontainers/base | docker               |
| .devcontainer/ansible/Dockerfile                        | 10   | GitHub release  | v1.5.9063     | docker-systemctl-replacement         | github-releases      |
| .devcontainer/ansible/Dockerfile                        | 17   | GitHub release  | v0.40.0       | nvm-sh/nvm                           | github-releases      |
| .devcontainer/ansible/Dockerfile                        | 19   | Node.js         | 24            | node                                 | node-version         |
| .devcontainer/ansible/devcontainer.json                 | 8    | Feature         | 2             | docker-in-docker                     | devcontainer-feature |
| .devcontainer/ansible/devcontainer.json                 | 13   | Feature         | 1             | common-utils                         | devcontainer-feature |
| compose.yaml                                            | 3    | Docker image    | 3.3.3         | prettier-image                       | docker               |
| compose.yaml                                            | 8    | Docker image    | amd64-469fada | ansible-lint                         | docker               |
| compose.yaml                                            | 14   | Docker image    | amd64-7487732 | yamllint                             | docker               |
| requirements.yml                                        | 2    | Git commit      | 09c14e2       | git-tools                            | git-refs             |
| requirements.yml                                        | 4    | Git tag         | 7.0.0         | ansible-role-visual-studio-code      | git-refs             |
| requirements.yml                                        | 6    | Git tag         | 0.2.12        | ansible-role-customize-gnome         | git-refs             |
| ci-inventory.yaml                                       | 109  | Custom          | 18.5.0        | cinc client_version                  | custom               |
| ci-inventory.yaml                                       | 110  | Docker image    | 18            | cincproject/cinc                     | docker               |
| ci-inventory.yaml                                       | 138  | SDKMAN          | 11.0.25-tem   | java                                 | sdkman               |
| ci-inventory.yaml                                       | 139  | SDKMAN          | 17.0.13-tem   | java                                 | sdkman               |
| ci-inventory.yaml                                       | 140  | SDKMAN          | 21.0.5-tem    | java                                 | sdkman               |
| ci-inventory.yaml                                       | 141  | SDKMAN          | 3.9.9         | maven                                | sdkman               |
| ci-inventory.yaml                                       | 142  | SDKMAN          | 7.6.4         | gradle                               | sdkman               |
| ci-inventory.yaml                                       | 143  | SDKMAN          | 8.12          | gradle                               | sdkman               |
| ci-inventory.yaml                                       | 181  | Scoop           | 19.00         | 7zip-helper                          | scoop                |
| playbook.yml                                            | 71   | Gnome ext       | v43           | sound-output-device-chooser          | gnome-extension      |
| playbook.yml                                            | 73   | Gnome ext       | v23           | wsmatrix                             | gnome-extension      |
| playbook.yml                                            | 75   | Gnome ext       | v34           | unblank                              | gnome-extension      |
| playbook.yml                                            | 77   | Gnome ext       | v48           | tiling-assistant                     | gnome-extension      |
| playbook.yml                                            | 79   | Gnome ext       | v41           | switcher                             | gnome-extension      |
| roles/basic_utils/tasks/main.yml                        | 332  | GitHub release  | 3.2.1         | fvm                                  | github-releases      |
| roles/bash/tasks/main.yml                               | 25   | Docker image    | 3.3.3         | prettier-image (alias)               | docker               |
| roles/fluxcd/tasks/main.yml                             | 14   | Docker image    | v2.2.3        | flux-cli                             | docker               |
| roles/homebrew/tasks/main.yaml                          | 48   | Homebrew        | 4.6.14        | homebrew                             | custom               |
| roles/kubectl/tasks/main.yml                            | 178  | Helm plugin     | 0.6.0         | helm-chartsnap                       | helm-plugin          |
| roles/kubectl/tasks/main.yml                            | 202  | Helm plugin     | 3.12.5        | helm-diff                            | helm-plugin          |
| roles/kubectl/tasks/main.yml                            | 208  | GitHub release  | v2.0.4        | kubectl-neat                         | github-releases      |
| roles/kubectl/tasks/main.yml                            | 216  | GitHub release  | v0.8.0        | kube-capacity                        | github-releases      |
| roles/kubectl/tasks/main.yml                            | 224  | GitHub release  | v0.0.47       | kubectl-modify-secret                | github-releases      |
| roles/lazygit/tasks/main.yml                            | 7    | GitHub release  | 0.58.0        | lazygit                              | github-releases      |
| roles/nvm/tasks/main.yaml                               | 12   | GitHub release  | v0.40.0       | nvm-sh/nvm (install)                 | github-releases      |
| roles/nvm/tasks/main.yaml                               | 41   | GitHub release  | v0.40.3       | nvm-sh/nvm (version)                 | github-releases      |
| roles/ollama/tasks/main.yml                             | 11   | Custom          | 0.15.2        | ollama                               | custom               |
| roles/ollama/tasks/main.yml                             | 12   | Model           | qwen2.5:3b    | ollama model                         | ollama-model         |
| roles/openwebui/files/docker-compose.yml                | 4    | Docker image    | v0.7.2        | open-webui                           | docker               |
| roles/php_development/tasks/main.yml                    | 6    | Default         | 8.4.10        | php                                  | custom               |
| roles/php_development/tasks/main.yml                    | 39   | Git commit      | adc99a7       | phpenv                               | git-refs             |
| roles/php_development/tasks/main.yml                    | 93   | Git commit      | e602902       | phpbuild                             | git-refs             |
| roles/vshn_emergency_credentials_receive/tasks/main.yml | 11   | GitHub release  | 1.2.1         | emergency-credentials-receive        | github-releases      |
| roles/vshn_tools/tasks/main.yml                         | 11   | GitHub release  | 0.5.0         | appcat-cli                           | github-releases      |
| roles/vshn_tools/tasks/main.yml                         | 13   | GitHub release  | 2.3.0         | k8ify                                | github-releases      |
| roles/vshn_tools/tasks/main.yml                         | 52   | Docker image    | v1.29.0       | commodore                            | docker               |
| roles/zed/tasks/main.yml                                | 123  | GitHub release  | v0.204.5      | zed                                  | github-releases      |

### Renovate Verification

A GitHub Action (`.github/workflows/verify-renovate.yml`) has been added that:

1. Validates `renovate.json` configuration
2. Runs Renovate in dry-run mode to extract all dependencies
3. Compares found dependencies against the snapshot in `.github/renovate-snapshot.json`
4. Fails the build if any expected dependencies are missing

**Snapshot contains 24 dependencies:**

- GitHub releases: docker-systemctl-replacement, nvm, fvm, homebrew, helm-chartsnap, helm-diff, kubectl-neat, kube-capacity, kubectl-modify-secret, lazygit, appcat-cli, k8ify, emergency-credentials-receive, zed
- Docker images: prettier-image, ansible-lint, yamllint, flux-cli, open-webui, commodore
- Git refs: git-tools, ansible-role-visual-studio-code, ansible-role-customize-gnome

### Snapshot Format

The snapshot is stored in **YAML format** (`.github/renovate-snapshot.yaml`) with:

- **Comments** on each dependency showing the Renovate comment format
- **Grouped by type**: Docker images, GitHub releases, Git refs
- **Human-readable** structure with file paths and current versions

### Update Script

**Location:** `scripts/update-renovate-snapshot.sh`

**Usage:**

```bash
# Check mode (CI/CD) - verifies all dependencies are found
./scripts/update-renovate-snapshot.sh --check

# Update mode - refreshes the snapshot
./scripts/update-renovate-snapshot.sh
```

**Features:**

- Parses Renovate dry-run output
- Compares against YAML snapshot
- Supports both check and update modes
- Used by GitHub Action with `--check` flag
- Can be run manually to update snapshot

### GitHub Action Integration

**Workflow:** `.github/workflows/verify-renovate.yml`

**Triggers:**

- Push to main (when renovate files change)
- Pull requests (when renovate files change)
- Manual trigger with `update_snapshot` option

**Steps:**

1. Validates `renovate.json` configuration
2. Runs `./scripts/update-renovate-snapshot.sh --check`
3. Fails if any expected dependencies are missing
4. Manual trigger can update snapshot via commit
