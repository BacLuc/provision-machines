"""
Pyinfra operations for HashiCorp Vault CLI installation with proper timeout handling.
"""

from pyinfra.api import operation
from pyinfra.api.exceptions import OperationError

# Import our custom operations
from pyinfra_collections.basic_utils.operations.apt import add_apt_repository_key, add_apt_repository
from pyinfra_collections.basic_utils.operations.packages import apt_install


@operation
def install_hashicorp_vault_cli(timeout: int = 30, **kwargs):
    """
    Install HashiCorp Vault CLI with proper timeout handling.
    
    Args:
        timeout: Timeout in seconds for web requests
    """
    # Add HashiCorp APT repository key
    key_result = add_apt_repository_key(
        url="https://apt.releases.hashicorp.com/gpg",
        keyring_path="/usr/share/keyrings/hashicorp-archive-keyring.asc",
        timeout=timeout,
        **kwargs
    )
    
    if not key_result.get("success"):
        raise OperationError(f"Failed to add HashiCorp APT repository key: {key_result.get('output', 'Unknown error')}")
    
    # Add HashiCorp APT repository
    repo_result = add_apt_repository(
        repo_url="https://apt.releases.hashicorp.com",
        filename="hashicorp",
        signed_by="/usr/share/keyrings/hashicorp-archive-keyring.asc",
        update_cache=True,
        **kwargs
    )
    
    if not repo_result.get("success"):
        raise OperationError(f"Failed to add HashiCorp APT repository: {repo_result.get('output', 'Unknown error')}")
    
    # Install Vault CLI
    install_result = apt_install(
        packages=["vault"],
        timeout=timeout,
        **kwargs
    )
    
    if not install_result.get("success"):
        raise OperationError(f"Failed to install Vault CLI: {install_result.get('output', 'Unknown error')}")
    
    return {
        "success": True,
        "changed": True,
        "output": "Successfully installed HashiCorp Vault CLI"
    }