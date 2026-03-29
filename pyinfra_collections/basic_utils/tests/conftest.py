"""
Test configuration for pyinfra collections.
"""

import pytest
import sys
import os

# Add the pyinfra_collections directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture
def mock_host():
    """Mock pyinfra host for testing."""
    from unittest.mock import MagicMock
    host = MagicMock()
    return host