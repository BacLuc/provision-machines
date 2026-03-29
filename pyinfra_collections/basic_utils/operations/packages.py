"""
Pyinfra operations for installing packages with proper timeout handling.
"""

import subprocess
import time
from typing import List, Optional

from pyinfra.api import operation
from pyinfra.api.exceptions import OperationError


@operation
def apt_install(
    packages: List[str],
    update_cache: bool = False,
    timeout: int = 300,
    retries: int = 3,
    retry_delay: int = 10,
    **kwargs,
):
    """
    Install packages using apt with proper timeout and retry handling.
    
    Args:
        packages: List of package names to install
        update_cache: Whether to update the package cache first
        timeout: Timeout in seconds for the installation command
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    if not packages:
        return {"success": True, "changed": False, "output": "No packages to install"}
    
    # Check if packages are already installed
    installed_packages = []
    packages_to_install = []
    
    try:
        result = subprocess.run(
            ["dpkg", "-l"] + packages,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        for package in packages:
            if f"ii  {package}" in result.stdout:
                installed_packages.append(package)
            else:
                packages_to_install.append(package)
                
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        # If we can't check installed packages, assume all need installation
        packages_to_install = packages
    
    if not packages_to_install:
        return {
            "success": True,
            "changed": False,
            "output": f"All packages already installed: {', '.join(installed_packages)}"
        }
    
    # Install packages with retry logic
    last_error = None
    for attempt in range(retries):
        try:
            cmd = ["apt-get", "install", "-y"]
            
            if update_cache:
                cmd.append("--update")
            
            cmd.extend(packages_to_install)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            return {
                "success": True,
                "changed": True,
                "output": f"Successfully installed packages: {', '.join(packages_to_install)}"
            }
            
        except subprocess.TimeoutExpired as e:
            last_error = f"Timeout installing packages: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except subprocess.CalledProcessError as e:
            last_error = f"Error installing packages: {e.stderr or str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
    
    raise OperationError(f"Failed to install packages after {retries} attempts. Last error: {last_error}")


@operation
def apt_update(timeout: int = 120, retries: int = 3, retry_delay: int = 5, **kwargs):
    """
    Update apt package cache with proper timeout and retry handling.
    
    Args:
        timeout: Timeout in seconds for the update command
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    last_error = None
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["apt-get", "update"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            return {
                "success": True,
                "changed": True,
                "output": "Successfully updated apt package cache"
            }
            
        except subprocess.TimeoutExpired as e:
            last_error = f"Timeout updating apt cache: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except subprocess.CalledProcessError as e:
            last_error = f"Error updating apt cache: {e.stderr or str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
    
    raise OperationError(f"Failed to update apt cache after {retries} attempts. Last error: {last_error}")


@operation
def download_and_install_deb(
    url: str,
    timeout: int = 30,
    install_timeout: int = 300,
    retries: int = 3,
    retry_delay: int = 5,
    **kwargs,
):
    """
    Download and install a .deb package with proper timeout handling.
    
    Args:
        url: URL to download the .deb package from
        timeout: Timeout in seconds for the download
        install_timeout: Timeout in seconds for the installation
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    import tempfile
    import os
    
    # Import the download operation
    from pyinfra_collections.basic_utils.operations.download import download_file
    
    # Download to temporary file
    with tempfile.NamedTemporaryFile(suffix=".deb", delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Download the package
        download_result = download_file(
            url=url,
            dest=temp_path,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay
        )
        
        if not download_result.get("success"):
            raise OperationError(f"Failed to download .deb package: {download_result.get('output', 'Unknown error')}")
        
        # Install the package with retry logic
        last_error = None
        for attempt in range(retries):
            try:
                result = subprocess.run(
                    ["apt-get", "install", "-y", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=install_timeout,
                    check=True
                )
                
                return {
                    "success": True,
                    "changed": True,
                    "output": f"Successfully installed .deb package from {url}"
                }
                
            except subprocess.TimeoutExpired as e:
                last_error = f"Timeout installing .deb package: {str(e)}"
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                    continue
                break
                
            except subprocess.CalledProcessError as e:
                last_error = f"Error installing .deb package: {e.stderr or str(e)}"
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                    continue
                break
        
        raise OperationError(f"Failed to install .deb package after {retries} attempts. Last error: {last_error}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)