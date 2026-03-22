# Hierarchical Configuration System Design (Pyinfra Native)

## Overview

You were absolutely right! Pyinfra has a robust built-in configuration system that we should leverage. Instead of creating a custom system, we'll use Pyinfra's native capabilities to achieve hierarchical configuration with proper precedence.

## Pyinfra's Native Configuration System

Pyinfra provides several built-in mechanisms for configuration:

### 1. Configuration Data Sources (in precedence order):

1. **Override Data** (`--data` flag) - Highest precedence
2. **Host-specific Data** - Per-host configuration 
3. **Group Data** - Group-based configuration
4. **Global Data** - Base configuration

### 2. Data Access Patterns:

```python
# In deploy.py or tasks
user = host.data.user  # Access configuration with fallback
enable_feature = host.data.get("enable_feature", False)  # With default
```

## Hierarchical Configuration Design

### Proposed Configuration Structure

```
provision-machines/
├── deploy.py                    # Main deployment entry point
├── config/                      # Configuration directory
│   ├── global.py               # Global defaults (lowest precedence)
│   ├── ci.py                   # CI-specific overrides  
│   └── machines/               # Machine-specific configs (gitignored)
│       ├── laptop.py           # Laptop configuration
│       ├── desktop.py          # Desktop configuration
│       └── server.py           # Server configuration
├── group_data/                 # Pyinfra group_data directory
│   ├── all.py                 # Base configuration for all hosts
│   ├── ci.py                  # CI environment group
│   ├── development.py         # Development role group
│   └── production.py          # Production role group
├── inventory/                  # Pyinfra inventory files
│   ├── local.py               # Local development inventory  
│   ├── ci.py                  # CI environment inventory
│   └── production.py          # Production inventory
└── pyinfra_collections/       # Future Pyinfra collections
```

### Configuration Precedence Implementation

1. **Global Base Configuration** (`config/global.py`)
   - Defines all default values
   - Serves as the foundation

2. **Environment Overrides** (`config/ci.py`, `group_data/ci.py`)
   - CI-specific settings
   - Applied when CI environment detected

3. **Machine-Specific Configuration** (`config/machines/*.py`)
   - Per-machine customizations
   - Highest precedence (besides CLI overrides)

### Implementation Example

#### 1. Global Base Configuration (`config/global.py`)

```python
# Global configuration defaults
# This serves as the base for all environments

# User configuration
USER = "vscode"
USER_GROUPS = ["sudo", "users"]

# Docker configuration
DOCKER_ENABLE = False
DOCKER_USER_GROUPS = ["docker"]
DOCKER_COMPOSE_ALIAS = True

# Basic utilities
BASIC_UTILS_ENABLE_DIRENV = False
BASIC_UTILS_ENABLE_KEEPASSXC = False
BASIC_UTILS_ENABLE_SIGNAL = False
BASIC_UTILS_ENABLE_SSH_CONFIG = False
BASIC_UTILS_ENABLE_SSH_AGENT = False
BASIC_UTILS_ENABLE_GCR_SSH_AGENT = False
BASIC_UTILS_ENABLE_JAVA = False
BASIC_UTILS_ENABLE_FLUTTER = False
BASIC_UTILS_ENABLE_GO = False
BASIC_UTILS_ENABLE_PYTHON = False
BASIC_UTILS_REMOVE_GHOSTTY = True

# SSH configuration
SSH_KEY_FILENAME = "id_ed25519"
SSH_KEY_COMMENT = "ssh-key"
GCR_SSH_AGENT_SOCKET = "/run/user/1000/gcr/ssh"
SSH_CONFIG_PATHS = ["./config.d/*"]

# Development tools
DEV_TOOLS_ENABLE_ZSH = False
DEV_TOOLS_ENABLE_NEOVIM = False
DEV_TOOLS_ENABLE_FZF = False
DEV_TOOLS_ENABLE_TMUX = False

# Global settings
DEBUG = False
VERBOSE = True
DRY_RUN = False
```

#### 2. CI Configuration (`config/ci.py`)

```python
# CI-specific configuration overrides
# Applied when GITHUB_ACTIONS or similar CI env vars are detected

import os

# Detect CI environment
CI_MODE = os.environ.get("GITHUB_ACTIONS") == "true"

if CI_MODE:
    # Override user for CI
    USER = "runner"
    USER_GROUPS = ["sudo", "users"]
    
    # Enable testing tools in CI
    DOCKER_ENABLE = True
    BASIC_UTILS_ENABLE_SSH_CONFIG = True
    SSH_CONFIG_PATHS = ["/tmp/config.d/*"]
    
    # Enable Python for testing
    BASIC_UTILS_ENABLE_PYTHON = True
    BASIC_UTILS_PYTHON_VENVS = [
        {
            "name": "test",
            "python_version": "3.11",
            "packages": ["pytest", "pytest-cov", "black", "ruff"]
        }
    ]
    
    # Enable only essential dev tools in CI
    DEV_TOOLS_ENABLE_NEOVIM = True
```

#### 3. Machine-Specific Configuration (`config/machines/laptop.py`)

```python
# Laptop-specific configuration
# This file is gitignored and customized per machine

import os

# Detect if we're on the right machine
if os.uname().nodename == "developer-laptop":
    # Override user configuration
    USER = "developer"
    USER_GROUPS = ["sudo", "users", "docker", "libvirt", "kvm"]
    
    # Enable full development stack
    DOCKER_ENABLE = True
    BASIC_UTILS_ENABLE_DIRENV = True
    BASIC_UTILS_ENABLE_KEEPASSXC = True
    BASIC_UTILS_ENABLE_SIGNAL = True
    BASIC_UTILS_ENABLE_SSH_CONFIG = True
    BASIC_UTILS_ENABLE_SSH_AGENT = True
    BASIC_UTILS_ENABLE_GCR_SSH_AGENT = True
    BASIC_UTILS_ENABLE_JAVA = True
    BASIC_UTILS_ENABLE_FLUTTER = True
    BASIC_UTILS_ENABLE_GO = True
    BASIC_UTILS_ENABLE_PYTHON = True
    BASIC_UTILS_REMOVE_GHOSTTY = True
    BASIC_UTILS_ENABLE_BAT = True
    
    # Python environments
    BASIC_UTILS_PYTHON_VENVS = [
        {
            "name": "dev",
            "python_version": "3.11",
            "requirements": "~/.dotfiles/python/requirements.txt"
        },
        {
            "name": "ml", 
            "python_version": "3.10",
            "packages": ["jupyter", "pandas", "numpy", "scikit-learn"]
        }
    ]
    
    # Enable all development tools
    DEV_TOOLS_ENABLE_ZSH = True
    DEV_TOOLS_ENABLE_NEOVIM = True
    DEV_TOOLS_ENABLE_FZF = True
    DEV_TOOLS_ENABLE_TMUX = True
    DEV_TOOLS_ENABLE_LAZYGIT = True
    
    # SSH customization
    SSH_KEY_FILENAME = "id_ed25519_laptop"
    SSH_KEY_COMMENT = "developer-laptop"
    SSH_CONFIG_PATHS = [
        "./config.d/*",
        "~/projects/*/configs/ssh/*",
        "~/.ssh/config.d/*"
    ]
```

### Main Deployment Script (`deploy.py`)

```python
#!/usr/bin/env python3
"""
Main Pyinfra deployment script with hierarchical configuration loading.
"""

import os
import sys
from pathlib import Path

# Add config directory to path to import configurations
sys.path.insert(0, str(Path(__file__).parent / "config"))

def load_hierarchical_config():
    """Load hierarchical configuration with proper precedence."""
    
    # 1. Load global defaults (lowest precedence)
    config = {}
    try:
        import global
        for key, value in vars(global).items():
            if not key.startswith('_'):
                config[key] = value
    except ImportError:
        print("Warning: global.py not found, using hardcoded defaults")
    
    # 2. Load environment-specific overrides
    if os.environ.get("GITHUB_ACTIONS") == "true":
        try:
            import ci
            for key, value in vars(ci).items():
                if not key.startswith('_'):
                    config[key] = value
        except ImportError:
            pass
    
    # 3. Load machine-specific overrides (highest precedence)
    machine_name = os.environ.get("PYINFRA_MACHINE_NAME") or os.uname().nodename
    machine_config_path = Path(__file__).parent / "config" / "machines" / f"{machine_name}.py"
    
    if machine_config_path.exists():
        try:
            # Load machine-specific config
            machine_spec = {}
            exec(machine_config_path.read_text(), machine_spec)
            
            for key, value in machine_spec.items():
                if not key.startswith('_'):
                    config[key] = value
        except Exception as e:
            print(f"Warning: Failed to load machine config: {e}")
    
    return config

def main():
    """Main deployment function."""
    
    # Load hierarchical configuration
    config = load_hierarchical_config()
    
    # Import Pyinfra
    from pyinfra.api import Inventory, deploy
    
    # Create inventory with configuration as override data
    # This gives it the highest precedence (even above machine-specific configs)
    inventory = Inventory(
        ("@local", config),  # Pass our merged config as override data
    )
    
    # Import and run main deployment
    # The config is now accessible via host.data
    # Example: user = host.data.USER, enable_docker = host.data.DOCKER_ENABLE
    
    # Import your actual deployment tasks here
    # from pyinfra_collections.basic_utils import main as basic_utils_main
    # basic_utils_main(inventory)
    
    print("Configuration loaded successfully:")
    for key, value in config.items():
        print(f"  {key} = {value}")

if __name__ == "__main__":
    main()
```

### Environment Variable Support

```python
# In your main deploy script, add environment variable support

def apply_env_overrides(config):
    """Apply environment variable overrides (highest precedence)."""
    
    env_mapping = {
        "USER": "USER",
        "DOCKER_ENABLE": "DOCKER_ENABLE", 
        "BASIC_UTILS_ENABLE_PYTHON": "BASIC_UTILS_ENABLE_PYTHON",
        # Add more mappings as needed
    }
    
    for env_var, config_key in env_mapping.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert string to appropriate type
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            
            config[config_key] = value
    
    return config
```

### Inventory Group Support

```python
# inventory/ci.py
# Pyinfra inventory file for CI environment

# Define CI-specific groups and configuration
ci_hosts = {
    "@local": {
        "groups": ["ci", "development"],
        # CI-specific host data
        "USER": "runner",
        "CI_MODE": True,
    }
}

# inventory/development.py
# Development environment inventory

dev_hosts = {
    "@local": {
        "groups": ["development"],
        # Development-specific data
        "DEBUG": True,
        "DEV_TOOLS_ENABLE_ALL": True,
    }
}
```

## Benefits of This Approach

1. **Uses Pyinfra Native Features**: Leverages pyinfra's built-in configuration system
2. **Clear Precedence**: predictably overrides in order
3. **Simple Implementation**: No custom config loader code needed
4. **CI Friendly**: Easy to override in CI environments
5. **Machine-Specific**: Gitignored files for per-machine customization
6. **Environment Detection**: Automatic detection of CI/machine context
7. **Backward Compatible**: Works with existing Pyinfra code

## Migration Plan for basic_utils

1. **Refactor group_data/all.py** -> Move to config/global.py
2. **Create CI config** -> config/ci.py 
3. **Create machine configs** -> config/machines/*.py
4. **Update deploy.py** -> Add hierarchical config loading
5. **Update tasks** -> Use new config style (host.data.USER vs host.data.user)
6. **Add environment variable support** -> For CI overrides

This approach gives us all the benefits we wanted while properly using Pyinfra's built-in capabilities rather than fighting against them!