"""External runtime locations; no credentials or asset bytes belong in source Git."""
import os
from pathlib import Path
SOURCE_ROOT=Path(__file__).resolve().parent
def location(name,default):return Path(os.environ.get(name,str(default))).expanduser().resolve()
DATASET_ROOT=location('PROOFPLAN_DATASET_ROOT',SOURCE_ROOT.parent/'datasets/junction-dataset')
MODEL_ROOT=location('PROOFPLAN_MODEL_ROOT',SOURCE_ROOT/'external')
RESULTS_ROOT=location('PROOFPLAN_RESULTS_ROOT',SOURCE_ROOT/'results')
CACHE_ROOT=location('PROOFPLAN_CACHE_ROOT',SOURCE_ROOT/'cache')
# Lifetime accounting is independent of movable results/cache roots.
BUDGET_LEDGER=location('PROOFPLAN_BUDGET_LEDGER',SOURCE_ROOT/'results/v2/gemini-ledger.sqlite3')
WORKER_URL=os.environ.get('PROOFPLAN_WORKER_URL','http://127.0.0.1:8766').rstrip('/')
if not WORKER_URL.startswith(('http://127.0.0.1:','http://localhost:')):raise ValueError('Worker must remain localhost; use an authenticated private tunnel for deployment')
