"""Tests for the index module."""

from unittest.mock import patch

import pytest

from typvend.index import parse_semver, resolve_latest_version


def test_parse_semver() -> None:
    """Tests that semver strings are parsed correctly into numeric tuples."""
    assert parse_semver("0.5.0") == (0, 5, 0)
    assert parse_semver("10.12.3") == (10, 12, 3)
    assert parse_semver("1.2") is None
    assert parse_semver("invalid") is None


@patch("typvend.index.fetch_index")
def test_resolve_latest_version(mock_fetch: pytest.Session) -> None:
    """Tests resolving the latest version of a package from mock index data."""
    mock_fetch.return_value = [  # type: ignore[attr-defined]
        {"name": "fontawesome", "version": "0.1.0"},
        {"name": "fontawesome", "version": "0.6.0"},
        {"name": "fontawesome", "version": "0.10.0"},  # test integer comparison
        {"name": "other-pkg", "version": "1.0.0"},
    ]

    assert resolve_latest_version("fontawesome") == "0.10.0"
    assert resolve_latest_version("other-pkg") == "1.0.0"

    with pytest.raises(ValueError, match="Package 'non-existent' not found"):
        resolve_latest_version("non-existent")
