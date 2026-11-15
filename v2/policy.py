from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Effective policy: explicit latest user approval overrides handoff cloud caps only."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=json.loads((ROOT/'config/policy.json').read_text())
POLICY['gemini'].update(api_requests_max=1000,estimated_cost_usd_max=100.0)
POLICY['authorization_override']='User explicitly approved 1000 HTTP requests and US$100 total including prior usage/reservations in latest task; no per-run reset.'
STATE=RESULTS_ROOT/'v2';STATE.mkdir(parents=True,exist_ok=True)
