#!/usr/bin/env bash

# Entrypoint: Syncs the uv environment then executes the given command.
#             Usage: ./entrypoint.sh <command> [args...]
#             Examples:
#               ./entrypoint.sh docent --help
#               ./entrypoint.sh docent-mcp
#               ./entrypoint.sh pytest

set -e
set -x

uv sync --all-extras

exec uv run "$@"
