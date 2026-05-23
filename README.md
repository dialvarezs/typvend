# typvend — Typst Package Vendoring CLI

`typvend` is a robust, lightweight, and fully typed Python CLI utility designed to vendor official Typst packages locally for offline development, sandboxed builds, or containerized production CI/CD workflows.

It is particularly useful for avoiding external HTTP downloads in `Containerfile` / `Dockerfile` configurations and unifying package versions across templates.

---

## Features

- **Double-Source of Truth Resolved:** Replaces manual package tarball fetching in Dockerfiles with a single, scanning-based automation step.
- **Dynamic File Scanning:** Recursively scans `.typ` files for `@preview/<pkg>:<version>` imports, extracts the distinct list, and downloads them in one go.
- **Explicit Vendoring:** Directly add packages via `add <pkg>[@<version>]` supporting explicit versions or `@latest` resolving (using the official packages index).
- **Directory Traversal Protection:** Implements strict path validation during archive decompression to prevent Zip Slip / Tar Slip vulnerabilities.
- **OS Path Resolution:** Integrates with `platformdirs` to default output to standard OS directories where Typst natively searches for packages.

---

## Installation

```bash
# Install and run instantly using uvx / pipx
uvx typvend --help
```

---

## CLI Usage

Global options:
- `-o`, `--output DIR` — Custom directory to extract packages (defaults to native OS Typst search path).
- `--namespace NS` — Custom namespace (defaults to `preview`).
- `-f`, `--force` — Re-download package even if it already exists.
- `-v`, `--verbose` — Enable verbose output logs.

### 1. Adding Packages Explicitly

```bash
# Download latest version of fontawesome
uvx typvend add fontawesome

# Download specific versions
uvx typvend add fontawesome@0.6.0 polario-frame@0.1.0
```

### 2. Scanning Project Directories

Recursively searches a file or directory for package imports and vendors all discovered packages in one command:

```bash
# Scan a templates directory and output packages to typst cache folder
uvx typvend scan ./templates

# Scan and output to a custom directory (e.g. for Docker cache stages)
uvx typvend scan ./templates --output /typst-packages
```

---

## Development Setup

`typvend` uses `uv` for package management, `just` for development commands, `ruff` for linting/formatting (all rules enabled), and `pyrefly` for static type checking.

### Dev Commands

All common tasks are defined in the `justfile`:

```bash
# Run all checks (format, lint, typecheck, test)
just check

# Format code
just format

# Lint code
just lint

# Type check using pyrefly
just typecheck

# Run pytest unit and integration tests
just test
```
