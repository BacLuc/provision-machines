"""
Pyinfra operations for managing APT repositories with proper timeout handling.
"""

import os
import tempfile
import time
from typing import Optional

import requests
from pyinfra.api import operation
from pyinfra.api.exceptions import OperationError


@operation
def add_apt_repository_key(
    url: str,
    keyring_path: str,
    timeout: int = 30,
    retries: int = 3,
    retry_delay: int = 5,
    **kwargs,
):
    """
    Add an APT repository key from a URL with proper timeout handling.
    
    Args:
        url: URL to download the key from
        keyring_path: Path where the keyring should be stored
        timeout: Timeout in seconds for the download request
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    # Create keyrings directory if it doesn't exist
    keyring_dir = os.path.dirname(keyring_path)
    if not os.path.exists(keyring_dir):
        os.makedirs(keyring_dir, mode=0o755, exist_ok=True)
    
    # Download with retry logic
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "pyinfra-apt-key/1.0"}
            )
            response.raise_for_status()
            
            # Write key to temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # Move temporary file to destination
            os.replace(temp_file_path, keyring_path)
            os.chmod(keyring_path, 0o644)
            
            return {
                "success": True,
                "changed": True,
                "output": f"Successfully added APT repository key from {url} to {keyring_path}"
            }
            
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout downloading APT key from {url}: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except requests.exceptions.RequestException as e:
            last_error = f"Error downloading APT key from {url}: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except Exception as e:
            last_error = f"Unexpected error downloading APT key from {url}: {str(e)}"
            break
    
    # Clean up temporary file if it exists
    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
    
    raise OperationError(f"Failed to download APT repository key after {retries} attempts. Last error: {last_error}")


@operation
def add_apt_repository(
    repo_url: str,
    filename: str,
    signed_by: Optional[str] = None,
    arch: Optional[str] = None,
    components: Optional[list] = None,
    update_cache: bool = True,
    **kwargs,
):
    """
    Add an APT repository to the system.
    
    Args:
        repo_url: Base URL of the repository
        filename: Name of the repository file (without .list extension)
        signed_by: Path to the keyring file for signature verification
        arch: Architecture for the repository
        components: List of repository components (e.g., ['main', 'contrib'])
        update_cache: Whether to update the package cache after adding
    """
    import subprocess
    import platform
    
    # Get system architecture if not specified
    if not arch:
        arch = subprocess.check_output(["dpkg", "--print-architecture"]).decode().strip()
    
    # Get OS release codename
    try:
        with open("/etc/os-release") as f:
            os_release = {}
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os_release[key] = value.strip('"')
        codename = os_release.get("VERSION_CODENAME")
    except (FileNotFoundError, KeyError):
        raise OperationError("Could not determine OS release codename")
    
    if not codename:
        raise OperationError("VERSION_CODENAME not found in /etc/os-release")
    
    # Default components if not specified
    if not components:
        components = ["main"]
    
    # Build repository line
    repo_parts = []
    repo_parts.append("deb")
    
    if arch:
        repo_parts.append(f"[arch={arch}]")
    
    if signed_by:
        repo_parts.append(f"signed-by={signed_by}")
    
    repo_parts.append(repo_url)
    repo_parts.append(codename)
    repo_parts.extend(components)
    
    repo_line = " ".join(repo_parts)
    
    # Write repository file
    repo_file_path = f"/etc/apt/sources.list.d/{filename}.list"
    
    # Check if repository already exists
    if os.path.exists(repo_file_path):
        with open(repo_file_path, "r") as f:
            existing_content = f.read().strip()
        
        if existing_content == repo_line:
            return {"success": True, "changed": False, "output": "Repository already exists"}
    
    # Write repository file
    try:
        with open(repo_file_path, "w") as f:
            f.write(repo_line + "\n")
        os.chmod(repo_file_path, 0o644)
        
        # Update package cache if requested
        if update_cache:
            subprocess.run(["apt-get", "update"], check=True, capture_output=True)
        
        return {
            "success": True,
            "changed": True,
            "output": f"Successfully added APT repository: {filename}"
        }
        
    except (IOError, OSError, subprocess.CalledProcessError) as e:
        raise OperationError(f"Failed to add APT repository: {str(e)}")