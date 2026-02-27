#!/usr/bin/env bash

# Lint: Lints all Python files.

set -e
set -x

uv run ruff check src tests
