#!/usr/bin/env bash
# Launch the Zephor RVM kiosk server.
# Uses the local virtualenv if present, otherwise the system python.
set -euo pipefail
cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

exec "$PY" app.py
