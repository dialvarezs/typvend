"""Module for fetching and parsing the Typst packages index.

This module provides functions to fetch the official package list and resolve
the latest version for any given package name.
"""

from typing import Any

import niquests

from typvend import __version__

# In-memory cache for index.json requests. Key is namespace.
_INDEX_CACHE: dict[str, list[dict[str, Any]]] = {}


def fetch_index(namespace: str = "preview") -> list[dict[str, Any]]:
    """Fetches the Typst package index for the given namespace.

    Args:
        namespace: The package namespace, e.g. "preview".

    Returns:
        A list of dictionaries containing package metadata.

    Raises:
        ValueError: If the response cannot be parsed or is invalid.
    """
    if namespace in _INDEX_CACHE:
        return _INDEX_CACHE[namespace]

    url = f"https://packages.typst.org/{namespace}/index.json"
    headers = {"User-Agent": f"typvend/{__version__}"}

    try:
        response = niquests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except niquests.RequestException as e:
        msg = f"Failed to fetch package index from {url}: {e}"
        raise ValueError(msg) from e

    if not isinstance(data, list):
        msg = f"Expected index.json to be a list, got {type(data)}"
        raise TypeError(msg)

    _INDEX_CACHE[namespace] = data
    return data


def parse_semver(version_str: str) -> tuple[int, int, int] | None:
    """Parses a semver version string into a tuple of integers.

    Args:
        version_str: A string of the form "major.minor.patch".

    Returns:
        A tuple (major, minor, patch), or None if the version is invalid.
    """
    parts = version_str.split(".")
    if len(parts) != 3:  # noqa: PLR2004
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def resolve_latest_version(pkg_name: str, namespace: str = "preview") -> str:
    """Resolves the latest version of a package from the Typst packages index.

    Args:
        pkg_name: The name of the package.
        namespace: The namespace to search.

    Returns:
        The latest version string (e.g. "0.6.0").

    Raises:
        ValueError: If the package is not found in the index.
        TypeError: If the upstream index response has an unexpected type.
    """
    index_data = fetch_index(namespace)
    versions: list[tuple[tuple[int, int, int], str]] = []
    for pkg in index_data:
        if pkg.get("name") == pkg_name:
            version = pkg.get("version")
            if isinstance(version, str):
                parsed = parse_semver(version)
                if parsed is not None:
                    versions.append((parsed, version))

    if not versions:
        msg = f"Package '{pkg_name}' not found in namespace '{namespace}'"
        raise ValueError(msg)

    return max(versions, key=lambda v: v[0])[1]
