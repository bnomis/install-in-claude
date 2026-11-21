#!/usr/bin/env bash
# Source this file: activates the project's .venv and puts src/ on PYTHONPATH.
THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(dirname "$THIS_DIR")

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
