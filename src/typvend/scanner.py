"""Module for scanning Typst files to find imported packages.

This module provides functionality to scan single .typ files or recursively
scan directories to identify all referenced packages in a given namespace.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)
PACKAGE_NAME_PATTERN = r"[a-zA-Z0-9_-]+"


def scan_file(file_path: Path, namespace: str = "preview") -> set[tuple[str, str]]:
    """Scans a single file for package imports in the given namespace.

    Matches imports like `@<namespace>/<pkg>:<version>`.

    Args:
        file_path: The path of the file to scan.
        namespace: The namespace to search for (e.g. "preview").

    Returns:
        A set of tuples (package_name, version).
    """
    pattern = re.compile(rf"@{re.escape(namespace)}/({PACKAGE_NAME_PATTERN}):(\d+\.\d+\.\d+)")

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        logger.warning("Could not read file %s: %s", file_path, e)
        return set()

    return {(match.group(1), match.group(2)) for match in pattern.finditer(content)}


def scan_path(path: Path, namespace: str = "preview") -> set[tuple[str, str]]:
    """Scans a file or recursively scans a directory for package imports.

    Args:
        path: Path to a file or directory.
        namespace: The namespace to search for (e.g. "preview").

    Returns:
        A set of tuples (package_name, version).
    """
    found: set[tuple[str, str]] = set()

    if path.is_file():
        return scan_file(path, namespace)

    if path.is_dir():
        for file in path.rglob("*.typ"):
            found.update(scan_file(file, namespace))

    return found
