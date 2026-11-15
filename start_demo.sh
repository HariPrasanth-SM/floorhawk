#!/usr/bin/env bash
set -euo pipefail
PROOFPLAN_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROOFPLAN_ROOT"
DEVICE=cpu
PORT=8765
WITH_VLM=0
while (($#)); do
  case "$1" in
    --device) DEVICE="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --vlm) WITH_VLM=1; shift;;
    *) echo "Usage: bash proofplan/start_demo.sh [--device cpu|0] [--port 8765] [--vlm]"; exit 2;;
  esac
done
PYTHON="$PROOFPLAN_ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo 'Missing proofplan/.venv. See DEMO_GUIDE.md.'; exit 1; }
[[ -f external/cubicasa-model.pkl && -f external/cubicasa-compatible/floortrans/post_prosessing.py ]] || { echo 'Run proofplan/.venv/bin/python proofplan/assets.py cubi and prepare_cubi_compat.py first.'; exit 1; }
"$PYTHON" -c 'import pymupdf, ifcopenshell, torch; print("Dependencies ready; CUDA:",torch.cuda.is_available())'
RUN_DIR="$PROOFPLAN_ROOT/results/demo-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
WORKER_PID=''
APP_PID=''
cleanup() {
  if [[ -n "$APP_PID" ]]; then kill "$APP_PID" 2>/dev/null || true; fi
  if [[ -n "$WORKER_PID" ]]; then kill "$WORKER_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
ARGS=(--device "$DEVICE" --port "$PORT")
if [[ "$WITH_VLM" == 1 ]]; then
  [[ -f external/qwen3-vl-2b/provenance.json ]] || { echo 'Run proofplan/.venv/bin/python proofplan/assets.py qwen first.'; exit 1; }
  "$PYTHON" -u vlm_worker.py --device cuda:0 --port 8766 >"$RUN_DIR/vlm.log" 2>&1 &
  WORKER_PID=$!
  ARGS+=(--vlm-url http://127.0.0.1:8766)
fi
"$PYTHON" -u app.py "${ARGS[@]}" >"$RUN_DIR/app.log" 2>&1 &
APP_PID=$!
echo "FloorHAWK: http://127.0.0.1:$PORT"
echo "Persistent logs: $RUN_DIR"
echo "Health: http://127.0.0.1:$PORT/health"
if [[ "$WITH_VLM" == 1 ]]; then echo 'VLM health: http://127.0.0.1:8766/health (blocked status means CUDA/model initialization is unavailable)'; fi
echo 'Press Ctrl+C to stop the app and optional worker.'
wait "$APP_PID"
