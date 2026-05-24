"""Command-line interface for the typvend tool.

This module sets up the argument parser, handles the subcommands 'add' and 'scan',
and configures logging.
"""

import argparse
import logging
import re
import sys
from collections.abc import Iterable
from pathlib import Path

import niquests
import platformdirs

from typvend.downloader import download_package
from typvend.index import resolve_latest_version
from typvend.scanner import scan_path

logger = logging.getLogger("typvend")
VENDORING_ERRORS = (ValueError, TypeError, niquests.RequestException, OSError)
PACKAGE_NAME_PATTERN = r"[a-zA-Z0-9_-]+"


def main() -> None:
    """Main entry point for the CLI."""
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-o", "--output", help="Custom output directory for vendored packages"
    )
    parent_parser.add_argument(
        "--namespace",
        default="preview",
        help="Package namespace (default: preview)",
    )
    parent_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Re-download package even if destination already exists",
    )
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output logging",
    )

    parser = argparse.ArgumentParser(description="typvend — Typst Package Vendoring CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add", parents=[parent_parser], help="Add explicit package(s) by name"
    )
    add_parser.add_argument(
        "packages",
        nargs="+",
        help="Package name(s) optionally with version (e.g. fontawesome or fontawesome@0.6.0)",
    )
    add_parser.set_defaults(func=handle_add)

    scan_parser = subparsers.add_parser(
        "scan",
        parents=[parent_parser],
        help="Scan files/directories and vendor all discovered package imports",
    )
    scan_parser.add_argument("path", help="Path to file or directory to scan for imports")
    scan_parser.set_defaults(func=handle_scan)

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )
    logger.setLevel(log_level)

    sys.exit(args.func(args))


def get_default_output() -> Path:
    """Returns the platform-specific default Typst package directory.

    Returns:
        A Path object pointing to the system package directory.
    """
    return platformdirs.user_data_path("typst") / "packages"


def parse_package_arg(pkg: str) -> tuple[str, str]:
    """Parses a package argument in format name[@version].

    Args:
        pkg: A string of the form "name" or "name@version".

    Returns:
        A tuple (name, version) where version is "latest" if not specified.

    Raises:
        ValueError: If the package name is empty or contains invalid characters.
    """
    name, separator, version = pkg.partition("@")
    if not separator or not version:
        version = "latest"

    if not name or not re.fullmatch(PACKAGE_NAME_PATTERN, name):
        msg = f"Invalid package name: '{name}'. Only alphanumeric, hyphens, underscores allowed."
        raise ValueError(msg)

    return name, version


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if all packages were successfully vendored, 1 otherwise.
    """
    # Type refinement
    packages: list[str] = args.packages
    package_specs: list[tuple[str, str, str]] = []

    for pkg_arg in packages:
        name, version = parse_package_arg(pkg_arg)
        package_specs.append((name, version, pkg_arg))

    return _vendor_packages(
        package_specs,
        args=args,
        resolve_latest=True,
    )


def handle_scan(args: argparse.Namespace) -> int:
    """Handles the 'scan' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if all discovered packages were successfully vendored, 1 otherwise.
    """
    namespace: str = args.namespace
    scan_target = Path(args.path)

    if not scan_target.exists():
        logger.error("Scan path does not exist: %s", scan_target)
        return 1

    logger.info("Scanning %s for package imports...", scan_target)
    packages = scan_path(scan_target, namespace)
    logger.info("Discovered %d package(s): %s", len(packages), packages)

    if not packages:
        logger.info("No packages found to vendor.")
        return 0

    package_specs = [(name, version, f"{name}:{version}") for name, version in sorted(packages)]
    return _vendor_packages(
        package_specs,
        args=args,
    )


def _vendor_packages(
    packages: Iterable[tuple[str, str, str]],
    *,
    args: argparse.Namespace,
    resolve_latest: bool = False,
) -> int:
    """Vendors package specs and returns a CLI status code."""
    namespace: str = args.namespace
    output_dir = Path(args.output) if args.output else get_default_output()
    force: bool = args.force
    failed = False

    for name, version, label in packages:
        try:
            resolved_version = version
            if resolve_latest and version == "latest":
                logger.info("Resolving latest version for %s...", name)
                resolved_version = resolve_latest_version(name, namespace)
                logger.info("Latest version resolved to %s", resolved_version)

            download_package(
                name=name,
                version=resolved_version,
                output_dir=output_dir,
                namespace=namespace,
                force=force,
            )
        except VENDORING_ERRORS:
            failed = True
            logger.error("Error vendoring package '%s'", label, exc_info=args.verbose)

    return 1 if failed else 0
