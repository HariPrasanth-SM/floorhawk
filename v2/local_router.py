from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Content/revision/prompt-keyed local task interpretation cache, including failures."""
import hashlib,json,time
from qa.common import ROOT,sha,write_json
from .routing import validate_routed
from .worker_client import request
from .supervisor import fresh_host

def interpret(question):
 identity={'question':question,'model_revision':'89644892e4d85e24eaac8bacfd4f463576704203','prompt_worker_sha':sha(ROOT/'vlm_worker.py'),'validator_sha':sha(ROOT/'v2/routing.py'),'mode':'local-routing','cache_policy':'valid-or-schema-abstained-v2'};key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();path=CACHE_ROOT/'v2-routing'/(key+'.json');t=time.perf_counter()
 if path.exists():r=json.loads(path.read_text());r['cache_hit']=True;r['retrieval_seconds']=time.perf_counter()-t;return r
 fresh_host();r=request({'mode':'route','question':question},90)
 if r.get('status')=='success':
  try:r['task']=validate_routed(r['task'])
  except ValueError:r={'status':'abstained','reason':'Generated task includes unexecutable filters or units; no qualifier silently ignored','revision':r.get('revision'),'peak_gpu_memory_bytes':r.get('peak_gpu_memory_bytes')}
 r.update(cache_hit=False,total_seconds=time.perf_counter()-t,identity=identity)
 if r.get('status') in ('success','abstained'):write_json(path,r)
 return r
