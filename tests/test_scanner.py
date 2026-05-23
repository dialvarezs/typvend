"""Tests for the scanner module."""

from pathlib import Path

from typvend.scanner import scan_file, scan_path


def test_scan_file(tmp_path: Path) -> None:
    """Tests scanning a single .typ file for package imports."""
    content = """
    #import "@preview/fontawesome:0.6.0": *
    #import "@preview/fontawesome:0.6.0": icon // Duplicate import should be deduped
    #import "@preview/other-pkg:1.2.3"
    #import "@preview/custom_pkg:0.0.1"
    #import "@other/ignored:0.1.0" // Different namespace, should be ignored
    """
    file_path = tmp_path / "main.typ"
    file_path.write_text(content, encoding="utf-8")

    packages = scan_file(file_path, namespace="preview")
    assert packages == {
        ("fontawesome", "0.6.0"),
        ("other-pkg", "1.2.3"),
        ("custom_pkg", "0.0.1"),
    }


def test_scan_path_dir(tmp_path: Path) -> None:
    """Tests scanning a directory recursively for .typ files."""
    dir_a = tmp_path / "subdir_a"
    dir_a.mkdir()
    file_a = dir_a / "a.typ"
    file_a.write_text('#import "@preview/pkg-a:0.1.0"', encoding="utf-8")

    dir_b = tmp_path / "subdir_b"
    dir_b.mkdir()
    file_b = dir_b / "b.typ"
    file_b.write_text('#import "@preview/pkg-b:2.0.0"', encoding="utf-8")

    # A non-typ file, should be ignored
    file_ignored = dir_b / "c.txt"
    file_ignored.write_text('#import "@preview/pkg-ignored:3.0.0"', encoding="utf-8")

    packages = scan_path(tmp_path, namespace="preview")
    assert packages == {
        ("pkg-a", "0.1.0"),
        ("pkg-b", "2.0.0"),
    }
