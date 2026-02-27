#!/usr/bin/env bash

# Setup:  Sets up a virtual environment.
#         Add the virtual environment to Jupyter.
#         Adds pre-commit hooks to git.

set -e
set -x

uv sync --all-extras --dev
uv run pre-commit install
