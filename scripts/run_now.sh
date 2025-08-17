#!/usr/bin/env bash
set -euo pipefail
# scripts/run_now.sh

DIR="$(cd "$(dirname "$0")"/.. && pwd)"
if [[ -x "$DIR/.venv/bin/python" ]]; then
  PY="$DIR/.venv/bin/python"
else
  PY="python3"
fi
exec "$PY" "$DIR/run_alert.py" "$@"