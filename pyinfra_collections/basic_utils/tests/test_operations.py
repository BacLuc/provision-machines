"""
Test cases for pyinfra operations with timeout handling.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import requests

from pyinfra_collections.basic_utils.operations.download import download_file
from pyinfra_collections.basic_utils.operations.apt import add_apt_repository_key
from pyinfra.api.exceptions import OperationError


class TestDownloadOperations:
    """Test download operations with timeout handling."""
    
    @patch('requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b'test data']
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = download_file(
                url="https://example.com/test.txt",
                dest=temp_path,
                timeout=30
            )
            
            assert result['success'] is True
            assert result['changed'] is True
            mock_get.assert_called_once()
            
            # Verify timeout was passed
            args, kwargs = mock_get.call_args
            assert kwargs['timeout'] == 30
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('requests.get')
    def test_download_file_timeout(self, mock_get):
        """Test download file timeout handling."""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(OperationError, match="Failed to download after 3 attempts"):
                download_file(
                    url="https://example.com/test.txt",
                    dest=temp_path,
                    timeout=30,
                    retries=3,
                    retry_delay=1
                )
            
            # Should have been called 3 times (retries)
            assert mock_get.call_count == 3
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('requests.get')
    def test_download_file_checksum_verification(self, mock_get):
        """Test download file with checksum verification."""
        # Mock successful response with known content
        test_content = b'test data for checksum'
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [test_content]
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Test with correct checksum (SHA512 of 'test data for checksum')
            import hashlib
            correct_checksum = hashlib.sha512(test_content).hexdigest()
            
            result = download_file(
                url="https://example.com/test.txt",
                dest=temp_path,
                timeout=30,
                checksum=correct_checksum,
                checksum_algorithm="sha512"
            )
            
            assert result['success'] is True
            assert result['changed'] is True
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('requests.get')
    def test_download_file_checksum_mismatch(self, mock_get):
        """Test download file with checksum mismatch."""
        # Mock successful response with content that doesn't match checksum
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b'wrong data']
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(OperationError, match="Checksum mismatch"):
                download_file(
                    url="https://example.com/test.txt",
                    dest=temp_path,
                    timeout=30,
                    checksum="wrong_checksum_value",
                    checksum_algorithm="sha512"
                )
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAptOperations:
    """Test APT operations with timeout handling."""
    
    @patch('requests.get')
    @patch('os.makedirs')
    @patch('os.chmod')
    def test_add_apt_repository_key_success(self, mock_chmod, mock_makedirs, mock_get):
        """Test successful APT repository key addition."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b'-----BEGIN PGP PUBLIC KEY BLOCK-----\ntest key data\n-----END PGP PUBLIC KEY BLOCK-----'
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = add_apt_repository_key(
                url="https://example.com/gpg.key",
                keyring_path=temp_path,
                timeout=30
            )
            
            assert result['success'] is True
            assert result['changed'] is True
            mock_get.assert_called_once()
            
            # Verify timeout was passed
            args, kwargs = mock_get.call_args
            assert kwargs['timeout'] == 30
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('requests.get')
    def test_add_apt_repository_key_timeout(self, mock_get):
        """Test APT repository key addition timeout handling."""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(OperationError, match="Failed to download APT repository key after 3 attempts"):
                add_apt_repository_key(
                    url="https://example.com/gpg.key",
                    keyring_path=temp_path,
                    timeout=30,
                    retries=3,
                    retry_delay=1
                )
            
            # Should have been called 3 times (retries)
            assert mock_get.call_count == 3
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)