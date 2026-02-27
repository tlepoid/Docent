#!/usr/bin/env bash

# Entrypoint: Syncs the uv environment and starts the application.
#             Defaults to the MCP server; pass a different command to override.
#             Usage: ./entrypoint.sh [command]
#             Examples:
#               ./entrypoint.sh                  # starts docent-mcp server
#               ./entrypoint.sh docent --help    # runs CLI

set -e
set -x

uv sync --all-extras

exec uv run "${@:-docent-mcp}"
