# typvend — Typst Package Vendoring CLI

[![PyPI](https://img.shields.io/pypi/v/typvend?style=flat-square)](https://pypi.org/project/typvend/)
[![PyVersions](https://img.shields.io/pypi/pyversions/typvend?style=flat-square)](https://github.com/dialvarezs/typvend)
[![Tests](https://img.shields.io/github/actions/workflow/status/dialvarezs/typvend/test.yml?style=flat-square)](https://github.com/dialvarezs/typvend/actions/workflows/test.yml)
![License](https://img.shields.io/github/license/dialvarezs/typvend?style=flat-square)

`typvend` is a lightweight Python CLI utility designed to vendor official Typst packages locally for offline development, sandboxed builds, or containerized production CI/CD workflows.

## Why?

Typst downloads packages on the fly at compile time with no official way to pre-download them.
This can be problematic for offline compilation and read-only production environments (like containers).
The solution is to either run the compilation once to fetch the packages or download them manually.

`typvend` simplifies this, downloading packages to the default Typst cache path or any directory you choose (then point Typst to it via `--package-cache-path`), in two ways:
- **Explicit:** `add <pkg>[@<version>]` — download specific packages by name, with a version or `@latest`.
- **Scan:** recursively find all `@preview/<pkg>:<version>` imports in `.typ` files and vendor them in one go.

## Usage

You can run `typvend` directly using [uv](https://docs.astral.sh/uv/).

```bash
uvx typvend --help
```

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
uvx typvend add fontawesome@0.5.0 cetz
```

### 2. Scanning Project Directories

Recursively searches a file or directory for package imports and vendors all discovered packages in one command:

```bash
# Scan a templates directory and output packages to typst cache folder
uvx typvend scan ./templates

# Scan and output to a custom directory (e.g. for Docker cache stages)
uvx typvend scan ./templates --output /typst-packages
```
