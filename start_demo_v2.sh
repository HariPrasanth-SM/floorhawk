#!/usr/bin/env bash
set -euo pipefail
export YOLO_OFFLINE=true HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 WANDB_MODE=disabled
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
MODE=local
PORT=8765
REPLAY=0
FAILURES=0
BUNDLE="$(.venv/bin/python -c 'from runtime_paths import RESULTS_ROOT; print(RESULTS_ROOT/"v2/replay-delivery")')"
DEFAULT_BUNDLE="$BUNDLE"
INSPECTION_DB="$(.venv/bin/python -c 'from runtime_paths import RESULTS_ROOT; print(RESULTS_ROOT/"inspection/index.sqlite3")')"
while (($#)); do
 case "$1" in
 --diagnostics) export PROOFPLAN_DIAGNOSTICS=1; shift;;
 --mode) MODE="$2"; shift 2;;
 --port) PORT="$2"; shift 2;;
 --replay) REPLAY=1; shift;;
 --include-failures) FAILURES=1; shift;;
 --bundle) BUNDLE="$2"; shift 2;;
 *) echo 'Usage: bash proofplan/start_demo_v2.sh [--mode local|hybrid] [--port 8765] [--replay --include-failures] [--bundle path]'; exit 2;;
 esac
done
if [[ "$REPLAY" == 1 ]]; then
 ARGS=(--bundle "$BUNDLE" --port "$PORT")
 if [[ "$FAILURES" == 1 ]]; then ARGS+=(--include-failures); fi
 if [[ "$BUNDLE" == "$DEFAULT_BUNDLE" && -f "$INSPECTION_DB" ]]; then
  INSPECT_ARGS=(--port "$PORT")
  if [[ "$FAILURES" == 1 ]]; then INSPECT_ARGS+=(--include-failures); fi
  exec .venv/bin/python -m inspection.replay "${INSPECT_ARGS[@]}"
 fi
 exec .venv/bin/python -m v2.replay "${ARGS[@]}"
fi
[[ "$MODE" == local || "$MODE" == hybrid ]] || { echo 'Choose local or hybrid; cloud-only is deferred.'; exit 2; }
export PROOFPLAN_DEFAULT_MODE="$MODE"
ARGS=(--gpu)
if .venv/bin/python -c 'from v2.supervisor import fresh_host;fresh_host()' >/dev/null 2>&1; then ARGS=(--host); fi
ARGS+=(--service)
exec .venv/bin/python -m v2.supervisor "${ARGS[@]}" -- .venv/bin/python app.py --device cpu --port "$PORT"
