#!/usr/bin/env bash

# Entrypoint: Syncs the uv environment then executes the given command.
#             With no arguments, runs the demo bond portfolio MCP server.
#             Usage: ./entrypoint.sh [command] [args...]
#             Examples:
#               ./entrypoint.sh                                                   # run demo MCP server
#               ./entrypoint.sh docent --service examples.demo_model.model:build_service scenarios
#               ./entrypoint.sh pytest

set -e
set -x

uv sync --all-extras

if [ $# -eq 0 ]; then
  exec uv run mcp dev examples/demo_model/run_mcp.py
else
  exec uv run "$@"
fi
