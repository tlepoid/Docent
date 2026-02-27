#!/usr/bin/env bash

# Format:   Auto-formats all Python files using Black.

set -e
set -x

uv run ruff format src tests
