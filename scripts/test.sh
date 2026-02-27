#!/usr/bin/env bash

# Test: Runs all automated tests with Pytest.

set -e
set -x


uv run pytest --cov=. --cov-report=term-missing
