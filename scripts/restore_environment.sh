#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
# Project-local only; no system Python, driver or DNS modifications.
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.venv/bin/python -m pip install -r requirements.txt -r requirements-qa.txt -r requirements-v2.txt
printf '%s\n' 'Environment restored. Restore verified artifacts and the EXISTING lifetime ledger before Hybrid use.'
