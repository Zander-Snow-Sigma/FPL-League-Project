"""Unit tests for the extract script."""

from extract import get_league_name


def test_get_league_name():
    """Tests the correct league name is returned."""
    raw_data = {'league': {'name': "test name"}, 'other': 'test'}
    assert get_league_name(raw_data) == "test name"
