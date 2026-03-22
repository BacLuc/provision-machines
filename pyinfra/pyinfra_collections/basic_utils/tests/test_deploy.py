"""Tests for basic_utils pyinfra deploy."""

from ..deploy import parse_bool


class TestDeploy:
    """Test basic_utils deploy."""

    def test_parse_bool_true_strings(self):
        """Test parsing of true-like string values."""
        assert parse_bool("true") is True
        assert parse_bool("True") is True
        assert parse_bool("TRUE") is True
        assert parse_bool("yes") is True
        assert parse_bool("1") is True

    def test_parse_bool_false_strings(self):
        """Test parsing of false-like string values."""
        assert parse_bool("false") is False
        assert parse_bool("False") is False
        assert parse_bool("no") is False
        assert parse_bool("0") is False
        assert parse_bool("") is False

    def test_parse_bool_boolean(self):
        """Test that boolean values pass through."""
        assert parse_bool(True) is True
        assert parse_bool(False) is False

    def test_parse_bool_other(self):
        """Test parsing of other types."""
        # None becomes False
        assert parse_bool(None) is False
        # Numbers become True (non-zero)
        assert parse_bool(1) is True
        assert parse_bool(0) is False
