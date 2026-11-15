from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Precompute actual referenced IFC geometry only; no inference."""
import json,time
from qa.common import ROOT,write_json
from .geometry_jobs import JOBS
paths=json.loads((RESULTS_ROOT/'inspection/ifc-inputs.json').read_text());results=[]
for path in paths:
 source=DATASET_ROOT/path;started=time.monotonic();r=JOBS.status(source,start=True)
 while r['status']in['queued','converting','busy']and time.monotonic()-started<125:
  time.sleep(1);r=JOBS.status(source,start=True)
 if r['status']in['queued','converting','busy']:JOBS.cancel(source)
 results.append({'source':path,'status':r['status'],'meshes':r.get('meshes'),'partial':r.get('partial'),'note':r.get('note')});print(results[-1],flush=True)
write_json(RESULTS_ROOT/'inspection/ifc-precomputed.json',results)
