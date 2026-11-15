#!/usr/bin/env bash
set -euo pipefail
export PROOFPLAN_RELEASE=v3
export PROOFPLAN_HOST_VISION="${PROOFPLAN_HOST_VISION:-1}"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/start_demo_v2.sh" "$@"
