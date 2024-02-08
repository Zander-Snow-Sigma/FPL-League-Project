"""Unit tests for the extract script."""

from extract import add_nums


def test_add_nums():
    """Tests for add function."""
    assert add_nums(1, 2) == 3
