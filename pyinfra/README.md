# Pyinfra Modules with Timeout Handling

This directory contains pyinfra modules that implement proper timeout handling for web requests, ensuring that deployments don't hang when remote endpoints have problems.

## Structure

```
pyinfra/
├── deploy.py                    # Main deployment script
├── pyinfra_collections/
│   ├── basic_utils/            # Basic utility operations
│   │   ├── operations/
│   │   │   ├── download.py     # File download with timeout
│   │   │   ├── apt.py          # APT repository management
│   │   │   └── packages.py     # Package installation
│   │   └── tests/
│   ├── development_tools/      # Development tool operations
│   │   └── operations/
│   │       ├── lazygit.py      # lazygit installation
│   │       └── git_lfs.py      # Git LFS installation
│   └── runtime_environments/   # Runtime environment operations
│       └── operations/
│           └── vault.py        # HashiCorp Vault CLI installation
```

## Features

### Timeout Handling
All web requests include configurable timeout parameters:
- `timeout`: Maximum time in seconds for a request (default: 30)
- `retries`: Number of retry attempts (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 5)

### Error Handling
- Proper exception handling for network timeouts
- Automatic retry with exponential backoff
- Clean error messages with context
- Temporary file cleanup on failure

### Checksum Verification
- Optional checksum verification for downloaded files
- Support for multiple hash algorithms (SHA512, SHA256, etc.)
- Automatic comparison before file replacement

## Usage

### Command Line
```bash
# Install HashiCorp Vault CLI with custom timeout
python pyinfra/deploy.py --install-vault --timeout=60 --retries=5

# Install lazygit with default settings
python pyinfra/deploy.py --install-lazygit

# Install Git LFS with custom retry settings
python pyinfra/deploy.py --install-git-lfs --retries=3 --retry-delay=10
```

### Python API
```python
from pyinfra_collections.basic_utils.operations.download import download_file
from pyinfra_collections.runtime_environments.operations.vault import install_hashicorp_vault_cli

# Download a file with timeout
result = download_file(
    url="https://example.com/file.zip",
    dest="/tmp/file.zip",
    timeout=30,
    retries=3,
    retry_delay=5
)

# Install Vault CLI
result = install_hashicorp_vault_cli(timeout=30)
```

## Operations

### Basic Utils

#### download_file
Download a file from a URL with proper timeout and retry handling.
```python
download_file(
    url="https://example.com/file.txt",
    dest="/path/to/destination.txt",
    timeout=30,
    retries=3,
    retry_delay=5,
    checksum="abc123...",  # Optional SHA512 checksum
    checksum_algorithm="sha512"
)
```

#### download_github_release
Download a specific asset from a GitHub release.
```python
download_github_release(
    repo="owner/repo",
    version="v1.0.0",
    asset_pattern="*.tar.gz",
    dest="/path/to/download.tar.gz",
    timeout=30
)
```

#### add_apt_repository_key
Add an APT repository key from a URL.
```python
add_apt_repository_key(
    url="https://example.com/gpg.key",
    keyring_path="/usr/share/keyrings/example.asc",
    timeout=30
)
```

#### apt_install
Install packages using apt with timeout handling.
```python
apt_install(
    packages=["package1", "package2"],
    update_cache=True,
    timeout=300,
    retries=3
)
```

### Development Tools

#### install_lazygit
Install lazygit from GitHub releases.
```python
install_lazygit(
    version="latest",
    install_dir="/usr/local/bin",
    timeout=30
)
```

#### install_git_lfs
Install Git LFS from GitHub releases.
```python
install_git_lfs(
    version="latest",
    install_dir="/usr/local/bin",
    timeout=30
)
```

### Runtime Environments

#### install_hashicorp_vault_cli
Install HashiCorp Vault CLI using official APT repository.
```python
install_hashicorp_vault_cli(timeout=30)
```

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install -r pyinfra_requirements.txt

# Run tests
pytest pyinfra_collections/basic_utils/tests/
```

## Requirements

- Python 3.8+
- pyinfra>=2.0
- requests>=2.25.0

## License

See the main repository license file.