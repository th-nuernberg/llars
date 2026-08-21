#!/bin/sh

set -eu

export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
export FLASK_APP="main"
export PATH="$PATH:/home/flaskuser/.local/bin"
export LLARS_RUNTIME_ROLE="${LLARS_RUNTIME_ROLE:-worker}"

exec python /app/worker_main.py
