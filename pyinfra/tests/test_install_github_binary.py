"""
Tests for the install_github_binary utility.
"""

import hashlib
import os
import tarfile
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from shared.install_github_binary import (
    _calculate_checksum,
    _detect_file_type,
    _extract_tar_archive,
    get_github_release_info,
    install_github_binary,
)


class TestCalculateChecksum:
    """Test checksum calculation functionality."""

    def test_calculate_sha256_checksum(self):
        """Test SHA256 checksum calculation."""
        # Create a temporary file with known content
        content = b"test content for checksum"
        expected_checksum = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            actual_checksum = _calculate_checksum(temp_file.name)

        # Clean up
        os.unlink(temp_file.name)

        assert actual_checksum == expected_checksum


class TestDetectFileType:
    """Test file type detection."""

    def test_detect_tar_gz_extension(self):
        """Test detecting .tar.gz files."""
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "tar.gz"

    def test_detect_tgz_extension(self):
        """Test detecting .tgz files."""
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "tar.gz"

    def test_detect_tar_extension(self):
        """Test detecting .tar files."""
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "tar"

    def test_detect_zip_extension(self):
        """Test detecting .zip files."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "zip"

    def test_detect_gz_extension(self):
        """Test detecting .gz files."""
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "gz"

    def test_detect_no_extension(self):
        """Test detecting files with no extension (defaults to binary)."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_type = _detect_file_type(temp_file.name)
            os.unlink(temp_file.name)
            assert file_type == "binary"


class TestExtractTarArchive:
    """Test tar archive extraction."""

    def test_extract_tar_with_strip_components(self):
        """Test extracting tar archive with directory stripping."""
        # Create a test tar file
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as temp_file:
            with tarfile.open(temp_file.name, "w") as tar:
                # Add a file in a subdirectory
                with tempfile.NamedTemporaryFile(delete=False) as content_file:
                    content_file.write(b"test binary content")
                    content_file.flush()

                    tar.add(content_file.name, arcname="subdirectory/test_binary")

            # Try to extract with strip_components=1
            with tempfile.TemporaryDirectory() as extract_dir:
                success = _extract_tar_archive(
                    temp_file.name, extract_dir, "test_binary", strip_components=1
                )

                assert success
                assert os.path.exists(os.path.join(extract_dir, "test_binary"))

        os.unlink(temp_file.name)

    def test_extract_no_matching_binary(self):
        """Test case where binary is not found in archive."""
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as temp_file:
            with tarfile.open(temp_file.name, "w") as tar:
                # Add a file with different name
                with tempfile.NamedTemporaryFile(delete=False) as content_file:
                    content_file.write(b"other content")
                    content_file.flush()

                    tar.add(content_file.name, arcname="other_binary")

            # Try to extract non-existent binary
            with tempfile.TemporaryDirectory() as extract_dir:
                success = _extract_tar_archive(
                    temp_file.name, extract_dir, "test_binary", strip_components=0
                )

                assert not success

        os.unlink(temp_file.name)


class TestGetGithubReleaseInfo:
    """Test GitHub API integration."""

    @patch("shared.install_github_binary.requests.get")
    def test_get_latest_release(self, mock_get):
        """Test getting latest release info."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "body": "Release notes",
            "published_at": "2023-01-01T00:00:00Z",
            "assets": [
                {
                    "name": "test-binary-linux-amd64",
                    "browser_download_url": "https://github.com/user/repo/releases/download/v1.0.0/test-binary-linux-amd64",
                    "size": 1024,
                }
            ],
        }
        mock_get.return_value = mock_response

        result = get_github_release_info("user/repo")

        assert result["tag_name"] == "v1.0.0"
        assert (
            result["download_url"]
            == "https://github.com/user/repo/releases/download/v1.0.0/test-binary-linux-amd64"
        )
        assert "assets" not in result

        mock_get.assert_called_once_with("https://api.github.com/repos/user/repo/releases")

    @patch("shared.install_github_binary.requests.get")
    def test_get_specific_version(self, mock_get):
        """Test getting specific version release info."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "body": "Release notes",
            "published_at": "2023-01-01T00:00:00Z",
            "assets": [
                {
                    "name": "test-binary",
                    "browser_download_url": "https://github.com/user/repo/releases/download/v1.0.0/test-binary",
                    "size": 512,
                }
            ],
        }
        mock_get.return_value = mock_response

        result = get_github_release_info("user/repo", version="v1.0.0")

        assert result["tag_name"] == "v1.0.0"
        assert (
            result["download_url"]
            == "https://github.com/user/repo/releases/download/v1.0.0/test-binary"
        )

        mock_get.assert_called_once_with(
            "https://api.github.com/repos/user/repo/releases/tags/v1.0.0"
        )

    @patch("shared.install_github_binary.requests.get")
    def test_get_release_with_asset_pattern(self, mock_get):
        """Test getting release with asset filtering."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "body": "Release notes",
            "published_at": "2023-01-01T00:00:00Z",
            "assets": [
                {
                    "name": "test-binary-darwin-amd64",
                    "browser_download_url": "https://github.com/user/repo/releases/download/v1.0.0/test-binary-darwin-amd64",
                    "size": 1024,
                },
                {
                    "name": "test-binary-linux-amd64",
                    "browser_download_url": "https://github.com/user/repo/releases/download/v1.0.0/test-binary-linux-amd64",
                    "size": 1024,
                },
            ],
        }
        mock_get.return_value = mock_response

        result = get_github_release_info("user/repo", asset_pattern="linux")

        assert "linux" in result["download_url"]

        mock_get.assert_called_once_with("https://api.github.com/repos/user/repo/releases")


class TestInstallGithubBinary:
    """Test the main install_github_binary function."""

    @patch("shared.install_github_binary.host")
    @patch("shared.install_github_binary.files.directory")
    @patch("shared.install_github_binary.server.shell")
    @patch("shared.install_github_binary.files.file")
    def test_install_binary_checksum_match(self, mock_file, mock_shell, mock_directory, mock_host):
        """Test installing binary when checksum matches (should skip)."""
        # Mock host.data and host.get_fact
        mock_host.data.get.return_value = "vscode"
        mock_host.get_fact.return_value = {"sha256": "correct_checksum"}

        result = install_github_binary(
            binary_name="test_binary",
            url="https://example.com/test_binary",
            binary_checksum="correct_checksum",
        )

        # Should return False (already up to date)
        assert result is False
        mock_directory.assert_not_called()  # Should not proceed with installation
        mock_host.get_fact.assert_called_once()

    @patch("shared.install_github_binary.host")
    @patch("shared.install_github_binary.files.directory")
    @patch("shared.install_github_binary.server.shell")
    @patch("shared.install_github_binary.files.file")
    def test_install_binary_no_checksum(self, mock_file, mock_shell, mock_directory, mock_host):
        """Test installing binary when no checksum provided."""
        # Mock that binary doesn't exist
        mock_host.data.get.return_value = "vscode"
        mock_host.get_fact.return_value = None

        # Mock directory creation
        mock_directory.return_value = None

        # Mock download and move operations
        mock_shell.side_effect = [
            None,  # Download command
            None,  # Move command
        ]

        # Mock file chmod
        mock_file.return_value = None

        result = install_github_binary(
            binary_name="test_binary", url="https://example.com/test_binary"
        )

        # Should return True (installed successfully)
        assert result is True
        mock_directory.assert_called_once()
        assert mock_shell.call_count == 2  # Download + move
        mock_file.assert_called_once_with(
            name="Make test_binary executable",
            path="/home/vscode/bin/test_binary",
            mode="755",
            user="vscode",
            group="vscode",
        )

    def test_install_binary_missing_params(self):
        """Test error handling for missing parameters."""
        with pytest.raises(ValueError, match="url and binary_name are required"):
            install_github_binary("", "")

        with pytest.raises(ValueError, match="url and binary_name are required"):
            install_github_binary(binary_name="test", url="")
