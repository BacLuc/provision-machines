"""
Pyinfra operations for downloading files with proper timeout handling.
"""

import os
import tempfile
import time
from typing import Optional

import requests
from pyinfra.api import operation
from pyinfra.api.exceptions import OperationError


@operation
def download_file(
    url: str,
    dest: str,
    timeout: int = 30,
    retries: int = 3,
    retry_delay: int = 5,
    checksum: Optional[str] = None,
    checksum_algorithm: str = "sha512",
    **kwargs,
):
    """
    Download a file from a URL with proper timeout and retry handling.

    Args:
        url: URL to download from
        dest: Destination file path
        timeout: Timeout in seconds for the download request
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
        checksum: Expected checksum for verification
        checksum_algorithm: Checksum algorithm to use
    """
    # Check if file already exists and matches checksum
    if os.path.exists(dest) and checksum:
        import hashlib
        
        with open(dest, "rb") as f:
            file_hash = hashlib.new(checksum_algorithm)
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        
        if file_hash.hexdigest() == checksum:
            return {"success": True, "changed": False, "output": f"File already exists and matches checksum: {dest}"}
    
    # Create destination directory if it doesn't exist
    dest_dir = os.path.dirname(dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    
    # Download with retry logic
    last_error = None
    for attempt in range(retries):
        try:
            # Download to temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                response = requests.get(
                    url,
                    timeout=timeout,
                    stream=True,
                    headers={"User-Agent": "pyinfra-download/1.0"}
                )
                response.raise_for_status()
                
                # Download in chunks to handle large files
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            # Verify checksum if provided
            if checksum:
                import hashlib
                
                with open(temp_file_path, "rb") as f:
                    file_hash = hashlib.new(checksum_algorithm)
                    for chunk in iter(lambda: f.read(4096), b""):
                        file_hash.update(chunk)
                
                if file_hash.hexdigest() != checksum:
                    os.unlink(temp_file_path)
                    raise OperationError(f"Checksum mismatch for downloaded file from {url}")
            
            # Move temporary file to destination
            os.replace(temp_file_path, dest)
            
            return {
                "success": True, 
                "changed": True, 
                "output": f"Successfully downloaded file from {url} to {dest}"
            }
            
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout downloading {url}: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except requests.exceptions.RequestException as e:
            last_error = f"Error downloading {url}: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except Exception as e:
            last_error = f"Unexpected error downloading {url}: {str(e)}"
            break
    
    # Clean up temporary file if it exists
    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
    
    raise OperationError(f"Failed to download {url} after {retries} attempts. Last error: {last_error}")


@operation
def download_github_release(
    repo: str,
    version: str,
    asset_pattern: str,
    dest: str,
    timeout: int = 30,
    retries: int = 3,
    retry_delay: int = 5,
    **kwargs,
):
    """
    Download a specific asset from a GitHub release with proper timeout handling.
    
    Args:
        repo: GitHub repository in format "owner/repo"
        version: Release version (tag)
        asset_pattern: Pattern to match the asset name (can use wildcards)
        dest: Destination file path
        timeout: Timeout in seconds for API requests
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    import fnmatch
    import json
    
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"
    
    # Get release information with retry logic
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(
                api_url,
                timeout=timeout,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "pyinfra-github-download/1.0"
                }
            )
            response.raise_for_status()
            release_data = response.json()
            
            # Find the matching asset
            assets = release_data.get("assets", [])
            matching_assets = [
                asset for asset in assets 
                if fnmatch.fnmatch(asset["name"], asset_pattern)
            ]
            
            if not matching_assets:
                raise OperationError(f"No asset matching pattern '{asset_pattern}' found in release {version}")
            
            # Download the first matching asset
            asset_url = matching_assets[0]["browser_download_url"]
            return download_file(
                url=asset_url,
                dest=dest,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
                **kwargs
            )
            
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout fetching GitHub release info: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except requests.exceptions.RequestException as e:
            last_error = f"Error fetching GitHub release info: {str(e)}"
            if attempt < retries - 1:
                time.sleep(retry_delay)
                continue
            break
            
        except (json.JSONDecodeError, KeyError) as e:
            last_error = f"Error parsing GitHub release data: {str(e)}"
            break
    
    raise OperationError(f"Failed to download GitHub release after {retries} attempts. Last error: {last_error}")