#!/usr/bin/env bash
set -euo pipefail
export YOLO_OFFLINE=true HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 WANDB_MODE=disabled
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p results/v2
read -r QUOTA HIGH MAX < <(.venv/bin/python -c 'import os,psutil; m=psutil.virtual_memory(); print(str(max(100,int(os.cpu_count()*40)))+"%",int(min(m.total*.50,m.available*.75)),int(min(m.total*.60,m.available*.85)))')
if systemctl --user show-environment >/dev/null 2>&1; then
  export PROOFPLAN_SCOPE=systemd-user-aggregate
  exec systemd-run --user --scope --unit=proofplan-v2-host -p "CPUQuota=$QUOTA" -p "MemoryHigh=$HIGH" -p "MemoryMax=$MAX" -p MemorySwapMax=0 .venv/bin/python -m v2.host_worker
else
  export PROOFPLAN_SCOPE=monitor-only-no-cgroup
  echo 'User systemd unavailable: using fail-closed monitored owned worker. No aggregate cgroup claim.'
  exec .venv/bin/python -m v2.host_worker
fi
