#!/usr/bin/env bash

# script/pre-commit:  Triggers all pre-commit checks.

set -e
set -x

uv run pre-commit run --all-files
