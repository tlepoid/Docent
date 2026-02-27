#!/usr/bin/env bash

# Type Check: Type checks all Python files using MyPy.

set -e
set -x

uv run ty check src tests
