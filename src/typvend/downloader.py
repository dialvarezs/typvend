"""Module for downloading and extracting Typst packages.

This module provides functions to fetch a package tarball from the Typst
repository, verify its paths to prevent directory traversal, and extract
its contents to the local vendor directory.
"""

import io
import logging
import sys
import tarfile
from pathlib import Path

import niquests

from typvend import __version__

logger = logging.getLogger(__name__)


def download_package(
    name: str,
    version: str,
    output_dir: Path,
    namespace: str = "preview",
    *,
    force: bool = False,
) -> bool:
    """Downloads and extracts a Typst package to the local directory.

    Args:
        name: The name of the package.
        version: The package version (e.g. "0.6.0").
        output_dir: The base vendor output directory.
        namespace: The namespace of the package (e.g. "preview").
        force: If True, overwrite the package even if it already exists.

    Returns:
        True if the package was downloaded and extracted, False if it was
        skipped because it already exists and force was False.

    Raises:
        ValueError: If a directory traversal is detected in the tarball.
        niquests.RequestException: If the package download fails.
    """
    dest_dir = output_dir / namespace / name / version
    if dest_dir.exists() and not force:
        logger.info(
            "Skipping package %s:%s (already exists at %s)",
            name,
            version,
            dest_dir,
        )
        return False

    url = f"https://packages.typst.org/{namespace}/{name}-{version}.tar.gz"
    logger.info("Downloading %s...", url)
    headers = {"User-Agent": f"typvend/{__version__}"}

    try:
        response = niquests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.content
        if content is None:
            msg = f"Failed to download package: no content received from {url}"
            raise ValueError(msg)
    except niquests.RequestException as e:
        logger.error("Failed to download package %s:%s: %s", name, version, e)
        raise

    logger.info("Extracting %s to %s...", name, dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_abs = dest_dir.resolve()

    tar_data = io.BytesIO(content)
    try:
        with tarfile.open(fileobj=tar_data, mode="r:gz") as tar:
            if sys.version_info >= (3, 12):
                # Python 3.12+ safe extraction filter
                tar.extractall(path=dest_dir, filter="data")
            else:
                # Manual validation for older versions
                for member in tar.getmembers():
                    member_path = (dest_dir / member.name).resolve()
                    if dest_abs not in member_path.parents and member_path != dest_abs:
                        msg = f"Attempted directory traversal in tarball: {member.name}"
                        raise ValueError(msg)
                tar.extractall(path=dest_dir)
    except (tarfile.TarError, ValueError) as e:
        msg = f"Attempted directory traversal in tarball: {e}"
        raise ValueError(msg) from e

    logger.info("Successfully vendored %s:%s", name, version)
    return True
