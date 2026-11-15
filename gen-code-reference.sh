#!/usr/bin/env bash
# Regenerate the docs' Code Reference pages (docs/code_reference/backend and
# frontend) from the source docstrings and JSDoc. Needs bun and uv.
set -euo pipefail
cd "$(dirname "$0")"

bun install
uv run --no-project --with-requirements requirements-docs.txt \
	python scripts/gen_code_reference.py "$@"
