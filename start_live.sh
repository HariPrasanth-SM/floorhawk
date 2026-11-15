#!/usr/bin/env bash
set -euo pipefail
export PROOFPLAN_PAIRED=1 PROOFPLAN_LARGE_DRAWINGS=1
export PROOFPLAN_HYBRID_EVIDENCE_V3="${PROOFPLAN_HYBRID_EVIDENCE_V3:-0}"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/start_demo_v3.sh" --mode local "$@"
