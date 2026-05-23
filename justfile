# Development commands for typvend

# Run all formatting and linting checks
check: format lint typecheck test

# Format code using ruff
format:
    uv run ruff format .

# Lint code using ruff
lint:
    uv run ruff check .

# Run type checking using pyrefly
typecheck:
    uv run pyrefly check

# Run unit tests using pytest
test:
    uv run pytest
