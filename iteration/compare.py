"""Frozen answer-free paired DEVELOPMENT run. Scoring is a separate process."""
import json,time,os,collections
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT,DATASET_ROOT
from .paired import Engine
O=Path(os.environ.get('PROOFPLAN_PAIR_RUN',str(RESULTS_ROOT/'iteration60')))
def main():
 from v2.budget import Ledger
 from demo_gpu import install
 from v3.pipeline import Pipeline
 a=json.loads((O/'authorization.json').read_text());manifest=json.loads((O/'selection.json').read_text());assert sha(O/'questions.jsonl')==manifest['questions_sha256'];qs=[json.loads(l)for l in(O/'questions.jsonl').open()];assert len(qs)<=40
 if(O/'local.predictions.jsonl').exists():raise RuntimeError('Preserve original candidate run; no silent resume/overwrite')
 before=Ledger().summary();write_json(O/'budget-before.json',before)
 if before['estimated_usd_max']-before['estimated_usd_reserved']<.024:raise RuntimeError('Insufficient verified remaining budget')
 install();pipeline=Pipeline('cpu',512);pipeline.set_cloud(False);engine=Engine(pipeline);start=time.perf_counter();local=[]
 # Do all local work first: the legacy Local egress guard patches process sockets.
 # It must never overlap cloud threads in this process.
 qs.sort(key=lambda q:(q['path'],q['sample_id']))
 with(O/'local.predictions.jsonl').open('x')as out:
  for q in qs:
   if time.time()>a['feature_stop_epoch']-180:break
   if set(q)!=set(['sample_id','path','question']):raise ValueError('Inference manifest must contain only IDs/path/question')
   t=time.perf_counter();r=engine.local(DATASET_ROOT/q['path'],q['question'],q['sample_id']);r.update(path=q['path'],question=q['question'],sample_id=q['sample_id']);out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush();local.append((q,r));print('Local',q['sample_id'],r['status'],round(time.perf_counter()-t,3),flush=True)
 write_json(O/'local-complete.json',{'n':len(local),'seconds':time.perf_counter()-start})
 hybrid=[]
 def cloud(item):
  q,r=item
  if time.time()>a['feature_stop_epoch']-100:return q,dict(status='provider_error',answer=None,unit=None,provider_invoked=False,provider_attempts=0,explanation='Cloud dispatch deadline reached; Local retained')
  return q,engine.hybrid(DATASET_ROOT/q['path'],q['question'],r)
 with ThreadPoolExecutor(max_workers=2)as pool,(O/'hybrid.predictions.jsonl').open('x')as out:
  futures=[pool.submit(cloud,item)for item in local]
  for f in as_completed(futures):
   q,r=f.result();r.update(sample_id=q['sample_id'],path=q['path'],question=q['question']);out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush();hybrid.append(r);print('Hybrid',q['sample_id'],r['status'],'HTTP',r.get('provider_attempts',0),flush=True)
 engine.close();after=Ledger().summary();write_json(O/'run.json',{'version':'paired-evidence-v1','sample_selection_sha256':sha(O/'selection.json'),'questions_sha256':sha(O/'questions.jsonl'),'local_n':len(local),'hybrid_n':len(hybrid),'configuration_sha256':engine.config_sha256,'total_seconds':time.perf_counter()-start,'provider_attempts_delta':after['requests_reserved']-before['requests_reserved'],'estimated_reservation_delta':after['estimated_usd_reserved']-before['estimated_usd_reserved'],'before':before,'after':after,'local_sha256':sha(O/'local.predictions.jsonl'),'hybrid_sha256':sha(O/'hybrid.predictions.jsonl'),'concurrency':2,'note':'No Local/cloud socket-guard overlap. One shared local bundle per drawing/config; per-question generation bounded2 attempts; no reference answers in inference.'});print('Finished paired run',flush=True)
if __name__=='__main__':main()
