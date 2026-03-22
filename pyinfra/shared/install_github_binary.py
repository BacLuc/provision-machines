"""
GitHub Binary Installer Utility

This module provides a utility for installing binaries from GitHub releases.
It replaces the functionality of the original Ansible github_release_binary role.
"""

import gzip
import hashlib
import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

import requests
from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server


def install_github_binary(
    binary_name: str,
    url: str,
    binary_checksum: Optional[str] = None,
    version: Optional[str] = None,
    strip_components: int = 0,
    asset_filter: Optional[str] = None,
    extract_dir: str = "~/bin",
    make_executable: bool = True,
    user: Optional[str] = None,
) -> bool:
    """
    Install a binary from a GitHub release with optional checksum verification.

    Args:
        binary_name: Name of the binary to install
        url: URL to download the binary/release artifact
        binary_checksum: Optional SHA256 checksum for verification
        version: Optional version to check (for informational purposes)
        strip_components: Number of leading directories to strip when extracting tar/zip
        asset_filter: Pattern to filter assets in multi-asset releases
        extract_dir: Directory to extract/install the binary to
        make_executable: Whether to make the binary executable
        user: User to install for (defaults to current user)

    Returns:
        bool: True if the binary was installed or updated, False if already up to date

    Raises:
        ValueError: If required parameters are missing or invalid
    """

    # Validate required parameters
    if not url or not binary_name:
        raise ValueError("url and binary_name are required parameters")

    # Set defaults
    if user is None:
        user = host.data.get("USER", "vscode")

    # Expand user home
    home = f"/home/{user}" if user != "root" else "/root"
    expanded_extract_dir = extract_dir.replace("~", home)

    binary_path = f"{expanded_extract_dir}/{binary_name}"

    # Check if binary already exists with correct checksum
    if binary_checksum:
        existing_binary = host.get_fact(File, path=binary_path)
        if existing_binary and existing_binary.get("sha256") == binary_checksum:
            # Binary exists with correct checksum, skip installation
            return False

    # Ensure target directory exists
    files.directory(
        name=f"Ensure {expanded_extract_dir} exists",
        path=expanded_extract_dir,
        mode="755",
        user=user,
        group=user,
    )

    # Download and install in temporary location first
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        download_url = url

        # Download the file
        server.shell(
            name=f"Download {binary_name} from GitHub release",
            commands=[f"curl -L -o {temp_file.name} '{download_url}'"],
        )

        # Verify checksum if provided
        if binary_checksum:
            downloaded_checksum = _calculate_checksum(temp_file.name)
            if downloaded_checksum != binary_checksum:
                os.unlink(temp_file.name)
                raise ValueError(
                    f"Checksum verification failed. Expected {binary_checksum}, got {downloaded_checksum}"
                )

        # Determine file type and extract/install appropriately
        file_type = _detect_file_type(temp_file.name)

        if file_type in ["tar", "tar.gz", "tgz"]:
            # Extract tar archive
            success = _extract_tar_archive(
                temp_file.name, expanded_extract_dir, binary_name, strip_components
            )
        elif file_type == "zip":
            # Extract zip archive
            success = _extract_zip_archive(
                temp_file.name, expanded_extract_dir, binary_name, strip_components
            )
        elif file_type in ["gz", "binary"]:
            # Direct binary or gzipped binary
            if file_type == "gz":
                success = _extract_gz_binary(temp_file.name, binary_path)
            else:
                server.shell(
                    name=f"Move binary to {binary_path}",
                    commands=[f"mv {temp_file.name} {binary_path}"],
                )
                success = True
        else:
            # Unknown file type, just copy it
            server.shell(
                name=f"Move unknown file type to {binary_path}",
                commands=[f"mv {temp_file.name} {binary_path}"],
            )
            success = True

        # Clean up temporary file
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        if not success:
            raise RuntimeError(f"Failed to extract/install {binary_name}")

    # Make binary executable if requested
    if make_executable:
        files.file(
            name=f"Make {binary_name} executable",
            path=binary_path,
            mode="755",
            user=user,
            group=user,
        )

    return True


def _calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _detect_file_type(file_path: str) -> str:
    """Detect the type of file based on extension and magic bytes."""
    # Check file extensions first
    if file_path.endswith(".tar.gz") or file_path.endswith(".tgz"):
        return "tar.gz"
    elif file_path.endswith(".tar"):
        return "tar"
    elif file_path.endswith(".zip"):
        return "zip"
    elif file_path.endswith(".gz"):
        return "gz"

    # Check magic bytes for binary files
    try:
        with open(file_path, "rb") as f:
            magic = f.read(4)

        if magic.startswith(b"\x1f\x8b"):  # gzip magic
            return "gz"
        elif magic.startswith(b"PK"):  # zip magic
            return "zip"
        else:
            # Assume it's a direct binary
            return "binary"
    except Exception:
        return "binary"


def _extract_tar_archive(
    archive_path: str, extract_dir: str, binary_name: str, strip_components: int
) -> bool:
    """Extract a tar archive to find and install the binary."""

    try:
        with tarfile.open(archive_path, "r:*") as tar:
            # Find the binary in the archive
            binary_found = False

            for member in tar.getmembers():
                member_path = Path(member.name)

                # Strip leading directories if requested
                if strip_components > 0:
                    parts = member_path.parts
                    if len(parts) <= strip_components:
                        continue
                    member_path = Path(*parts[strip_components:])

                # Check if this is our binary
                if member_path.name == binary_name:
                    # Extract the binary
                    tar.extract(member, extract_dir)

                    # Move to correct location if it has subdirectories
                    extracted_path = Path(extract_dir) / member.name
                    final_path = Path(extract_dir) / binary_name

                    if extracted_path != final_path:
                        extracted_path.rename(final_path)

                    binary_found = True
                    break

            return binary_found

    except Exception as e:
        print(f"Failed to extract tar archive: {e}")
        return False


def _extract_zip_archive(
    archive_path: str, extract_dir: str, binary_name: str, strip_components: int
) -> bool:
    """Extract a zip archive to find and install the binary."""

    try:
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            binary_found = False

            for member in zip_file.infolist():
                member_path = Path(member.filename)

                # Strip leading directories if requested
                if strip_components > 0:
                    parts = member_path.parts
                    if len(parts) <= strip_components:
                        continue
                    member_path = Path(*parts[strip_components:])

                # Check if this is our binary
                if member_path.name == binary_name:
                    # Extract the binary
                    zip_file.extract(member, extract_dir)

                    # Move to correct location if it has subdirectories
                    extracted_path = Path(extract_dir) / member_path
                    final_path = Path(extract_dir) / binary_name

                    if extracted_path != final_path:
                        extracted_path.rename(final_path)

                    binary_found = True
                    break

            return binary_found

    except Exception as e:
        print(f"Failed to extract zip archive: {e}")
        return False


def _extract_gz_binary(archive_path: str, output_path: str) -> bool:
    """Extract a gzipped binary file."""

    try:
        with gzip.open(archive_path, "rb") as gz_file:
            with open(output_path, "wb") as output_file:
                output_file.write(gz_file.read())
        return True

    except Exception as e:
        print(f"Failed to extract gzipped binary: {e}")
        return False


def get_github_release_info(
    repo: str, version: Optional[str] = None, asset_pattern: Optional[str] = None
) -> dict[str, Any]:
    """
    Get GitHub release information from the GitHub API.

    Args:
        repo: Repository in format "owner/repo"
        version: Specific version tag (if None, gets latest)
        asset_pattern: Pattern to filter assets (e.g., "*linux*amd64*")

    Returns:
        Dictionary with release information including download URLs

    Raises:
        requests.RequestException: If API request fails
        ValueError: If release or asset not found
    """

    api_url = f"https://api.github.com/repos/{repo}/releases"

    if version:
        api_url += f"/tags/{version}"

    response = requests.get(api_url)
    response.raise_for_status()

    if version:
        # Single release
        releases = [response.json()]
    else:
        # Get latest release
        releases = [response.json()]  # GitHub API returns latest when no tag specified
        if not releases or "assets" not in releases[0]:
            raise ValueError(f"No releases found for {repo}")

    release = releases[0]

    # Find matching asset
    asset = None
    if asset_pattern:
        for candidate_asset in release.get("assets", []):
            if asset_pattern in candidate_asset["name"].lower():
                asset = candidate_asset
                break
    elif len(release.get("assets", [])) >= 1:
        asset = release["assets"][0]
    else:
        raise ValueError(f"No assets found in release for {repo}")

    return {
        "tag_name": release["tag_name"],
        "release_name": release.get("name", ""),
        "body": release.get("body", ""),
        "published_at": release.get("published_at", ""),
        "download_url": asset["browser_download_url"],
        "asset_name": asset["name"],
        "size": asset["size"],
        "checksum": None,  # Would need to calculate or get from release notes
    }
