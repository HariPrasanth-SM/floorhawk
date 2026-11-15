"""Second bounded contract check on SAME frozen16 Local answers; no extraction rerun."""
import json,time,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT,DATASET_ROOT
from v2.budget import Ledger
from .paired import Engine,VERSION
O=RESULTS_ROOT/'iteration60/paired-v2';BASE=RESULTS_ROOT/'iteration60/paired-v1'
def main():
 from v3.pipeline import Pipeline
 O.mkdir(exist_ok=True)
 if(O/'local.predictions.jsonl').exists():raise RuntimeError('Preserve candidate records')
 a=json.loads((BASE/'authorization.json').read_text());before=Ledger().summary()
 if before['estimated_usd_max']-before['estimated_usd_reserved']<.4:raise RuntimeError('Not enough verified budget for worst-case32 requests')
 total_before=json.loads((BASE/'budget-before.json').read_text())['requests_reserved']
 if before['requests_reserved']-total_before>48:raise RuntimeError('Iteration80-request cap would be exceeded')
 for name in ['questions.jsonl','selection.json','local.predictions.jsonl']:shutil.copyfile(BASE/name,O/name)
 local=[json.loads(l)for l in(O/'local.predictions.jsonl').open()];write_json(O/'budget-before.json',before);pipeline=Pipeline('cpu',512);pipeline.set_cloud(False);engine=Engine(pipeline);started=time.perf_counter()
 def call(row):
  if time.time()>a['feature_stop_epoch']-100:raise RuntimeError('Dispatch window closed')
  result=engine.hybrid(DATASET_ROOT/row['path'],row['question'],row);result.update(sample_id=row['sample_id'],path=row['path'],question=row['question']);return result
 with ThreadPoolExecutor(max_workers=2)as pool,(O/'hybrid.predictions.jsonl').open('x')as out:
  for f in as_completed([pool.submit(call,row)for row in local]):
   r=f.result();out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush();print('V2 Hybrid',r['sample_id'],r['status'],'HTTP',r.get('provider_attempts'),flush=True)
 engine.close();after=Ledger().summary();write_json(O/'run.json',{'version':VERSION,'local_n':len(local),'hybrid_n':len(local),'local_source_run':'paired-v1','local_recomputed':False,'local_sha256':sha(O/'local.predictions.jsonl'),'hybrid_sha256':sha(O/'hybrid.predictions.jsonl'),'configuration_sha256':engine.config_sha256,'source_sha256':sha(ROOT/'iteration/paired.py'),'before':before,'after':after,'provider_attempts_delta':after['requests_reserved']-before['requests_reserved'],'estimated_reservation_delta':after['estimated_usd_reserved']-before['estimated_usd_reserved'],'total_seconds':time.perf_counter()-started,'note':'Fresh Hybrid generation, same saved Local evidence. Optional source-bounded ROI proposal preserved as unverified; reference answers never loaded.'})
if __name__=='__main__':main()
