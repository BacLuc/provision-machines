"""
Pyinfra operations for lazygit installation with proper timeout handling.
"""

from pyinfra.api import operation
from pyinfra.api.exceptions import OperationError

# Import our custom operations
from pyinfra_collections.basic_utils.operations.download import download_github_release
from pyinfra_collections.basic_utils.operations.packages import apt_install


@operation
def install_lazygit(
    version: str = "latest",
    install_dir: str = "/usr/local/bin",
    timeout: int = 30,
    **kwargs,
):
    """
    Install lazygit with proper timeout handling.
    
    Args:
        version: Version of lazygit to install
        install_dir: Directory to install the binary
        timeout: Timeout in seconds for web requests
    """
    import os
    import tempfile
    import tarfile
    import subprocess
    
    # Install dependencies
    deps_result = apt_install(
        packages=["tar", "wget"],
        timeout=timeout,
        **kwargs
    )
    
    if not deps_result.get("success"):
        raise OperationError(f"Failed to install dependencies: {deps_result.get('output', 'Unknown error')}")
    
    # Determine architecture
    try:
        arch_result = subprocess.run(["uname", "-m"], capture_output=True, text=True, check=True)
        arch = arch_result.stdout.strip()
        
        # Map architecture names
        if arch == "x86_64":
            arch = "x86_64"
        elif arch == "aarch64":
            arch = "arm64"
        else:
            raise OperationError(f"Unsupported architecture: {arch}")
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise OperationError("Could not determine system architecture")
    
    # Download lazygit release
    asset_pattern = f"lazygit_{version}_Linux_{arch}.tar.gz"
    
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Download the release
        download_result = download_github_release(
            repo="jesseduffield/lazygit",
            version=version,
            asset_pattern=asset_pattern,
            dest=temp_path,
            timeout=timeout,
            **kwargs
        )
        
        if not download_result.get("success"):
            raise OperationError(f"Failed to download lazygit: {download_result.get('output', 'Unknown error')}")
        
        # Extract the binary
        with tarfile.open(temp_path, "r:gz") as tar:
            # Find the lazygit binary
            for member in tar.getmembers():
                if member.name.endswith("lazygit") and not member.isdir():
                    # Extract to temporary location first
                    tar.extract(member, path="/tmp")
                    extracted_path = f"/tmp/{member.name}"
                    break
            else:
                raise OperationError("Could not find lazygit binary in the archive")
        
        # Install the binary
        install_path = os.path.join(install_dir, "lazygit")
        
        # Move binary to install location
        subprocess.run(["sudo", "mv", extracted_path, install_path], check=True)
        subprocess.run(["sudo", "chmod", "+x", install_path], check=True)
        
        return {
            "success": True,
            "changed": True,
            "output": f"Successfully installed lazygit {version} to {install_path}"
        }
        
    except Exception as e:
        raise OperationError(f"Failed to install lazygit: {str(e)}")
        
    finally:
        # Clean up temporary files
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        extracted_path = "/tmp/lazygit"
        if os.path.exists(extracted_path):
            os.unlink(extracted_path)