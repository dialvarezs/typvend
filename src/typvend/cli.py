"""Command-line interface for the typvend tool.

This module sets up the argument parser, handles the subcommands 'add' and 'scan',
and configures logging.
"""

import argparse
import logging
import sys
from pathlib import Path

import platformdirs

from typvend.downloader import download_package
from typvend.index import resolve_latest_version
from typvend.scanner import scan_path

logger = logging.getLogger("typvend")


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
    """
    if "@" in pkg:
        parts = pkg.split("@", 1)
        name = parts[0]
        version = parts[1] or "latest"
    else:
        name = pkg
        version = "latest"
    return name, version


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if all packages were successfully vendored, 1 otherwise.
    """
    namespace: str = args.namespace
    output_dir = Path(args.output) if args.output else get_default_output()
    force: bool = args.force

    failed = False

    # Type refinement
    packages: list[str] = args.packages

    for pkg_arg in packages:
        name, version = parse_package_arg(pkg_arg)
        try:
            if version == "latest":
                logger.info("Resolving latest version for %s...", name)
                version = resolve_latest_version(name, namespace)
                logger.info("Latest version resolved to %s", version)

            download_package(
                name=name,
                version=version,
                output_dir=output_dir,
                namespace=namespace,
                force=force,
            )
        except Exception as e:
            failed = True
            logger.error("Error vendoring package '%s': %s", pkg_arg, e)
            if args.verbose:
                logger.exception(e)

    return 1 if failed else 0


def handle_scan(args: argparse.Namespace) -> int:
    """Handles the 'scan' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if all discovered packages were successfully vendored, 1 otherwise.
    """
    namespace: str = args.namespace
    output_dir = Path(args.output) if args.output else get_default_output()
    force: bool = args.force
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

    failed = False
    for name, version in sorted(packages):
        try:
            download_package(
                name=name,
                version=version,
                output_dir=output_dir,
                namespace=namespace,
                force=force,
            )
        except Exception as e:
            failed = True
            logger.error("Error vendoring package '%s:%s': %s", name, version, e)
            if args.verbose:
                logger.exception(e)

    return 1 if failed else 0


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
        help=("Package name(s) optionally with version (e.g. fontawesome or fontawesome@0.6.0)"),
    )

    scan_parser = subparsers.add_parser(
        "scan",
        parents=[parent_parser],
        help="Scan files/directories and vendor all discovered package imports",
    )
    scan_parser.add_argument("path", help="Path to file or directory to scan for imports")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )
    logger.setLevel(log_level)

    if args.command == "add":
        code = handle_add(args)
    elif args.command == "scan":
        code = handle_scan(args)
    else:
        code = 1

    sys.exit(code)
