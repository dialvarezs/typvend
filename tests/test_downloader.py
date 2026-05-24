"""Tests for the downloader module."""

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from typvend.downloader import download_package


def create_mock_tarball(files: dict[str, bytes]) -> bytes:
    """Helper to create a gzip-compressed tarball in memory.

    Args:
        files: A dictionary mapping filenames to their byte contents.

    Returns:
        The gzip-compressed bytes of the tar archive.
    """
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        for filename, content in files.items():
            info = tarfile.TarInfo(name=filename)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return out.getvalue()


@patch("niquests.get")
def test_download_package(mock_get: MagicMock, tmp_path: Path) -> None:
    """Tests successful package download, extraction, and override behavior."""
    expected_forced_download_count = 2
    mock_tar = create_mock_tarball({"lib.typ": b"// lib content", "typst.toml": b"name = 'pkg'"})
    mock_response = MagicMock()
    mock_response.content = mock_tar
    mock_get.return_value = mock_response

    output_dir = tmp_path / "vendor"

    # Download first time
    download_package("pkg", "0.1.0", output_dir=output_dir, force=False)

    pkg_dir = output_dir / "preview" / "pkg" / "0.1.0"
    assert (pkg_dir / "lib.typ").read_text(encoding="utf-8") == "// lib content"
    assert (pkg_dir / "typst.toml").read_text(encoding="utf-8") == "name = 'pkg'"
    assert mock_get.call_count == 1

    # Try downloading again without force (should skip)
    download_package("pkg", "0.1.0", output_dir=output_dir, force=False)
    assert mock_get.call_count == 1

    # Try downloading again with force
    download_package("pkg", "0.1.0", output_dir=output_dir, force=True)
    assert mock_get.call_count == expected_forced_download_count


@patch("niquests.get")
def test_download_package_directory_traversal(mock_get: MagicMock, tmp_path: Path) -> None:
    """Tests that directory traversal in a tarball raises a ValueError."""
    mock_tar = create_mock_tarball({"../../traversal.txt": b"infiltrated"})
    mock_response = MagicMock()
    mock_response.content = mock_tar
    mock_get.return_value = mock_response

    output_dir = tmp_path / "vendor"

    with pytest.raises((ValueError, tarfile.OutsideDestinationError)):
        download_package("pkg", "0.1.0", output_dir=output_dir, force=True)
