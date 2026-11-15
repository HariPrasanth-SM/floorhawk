from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Answer-free checkpointed A1/A2 runner; frozen QA source and bounded cloud subset."""
import argparse,json,time,resource,shutil,os
from pathlib import Path
from .pipeline import Pipeline
from .policy import ROOT,STATE
from qa.common import sha,write_json,versions

def main():
 p=argparse.ArgumentParser();p.add_argument('--questions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['local','hybrid'],default='local');p.add_argument('--no-ocr',action='store_true');p.add_argument('--no-structural',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args();rows=[json.loads(l) for l in a.questions.open()]
 if any(set(r)!={'sample_id','path','question'} for r in rows):raise ValueError('Inference fields must be sample_id/path/question only')
 if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs')
 if a.mode=='hybrid' and (len(rows)>40 or sha(a.questions)!=sha(ROOT/'benchmarks/v2/paired.questions.jsonl')):raise ValueError('Only frozen40 paired development rows authorized for batch cloud')
 sources={str(f.relative_to(ROOT)):sha(f) for folder in ['v2','qa'] for f in sorted((ROOT/folder).glob('*.py'))};settings={'questions_sha256':sha(a.questions),'mode':a.mode,'ocr':not a.no_ocr,'structural':not a.no_structural,'sources':sources}
 a.output.mkdir(parents=True,exist_ok=a.resume);pred=a.output/'predictions.jsonl';done=set()
 if a.resume:
  old=json.loads((a.output/'run.json').read_text())
  if old['settings']!=settings:raise ValueError('Source/settings mismatch: choose a fresh output')
  if pred.exists():
   raw=pred.read_text().splitlines();valid=[]
   for i,line in enumerate(raw):
    try:r=json.loads(line)
    except json.JSONDecodeError:
     if i!=len(raw)-1:raise
     (a.output/'interrupted-tail.txt').write_text(line);continue
    done.add(r['sample_id']);valid.append(line)
   if len(valid)!=len(raw):pred.write_text('\n'.join(valid)+'\n')
  if len(done)==len(rows) and (a.output/'complete.json').exists():print('Already completed; preserved.');return
 else:
  write_json(a.output/'run.json',{'settings':settings,'dependencies':versions(),'started':time.time(),'n':len(rows),'cache_policy':'Shared fact caches; stage cache flags retained. Paired warm evaluation after smoke/prefill; no uncached latency equivalence claim.'})
  for folder in ['v2','qa']:shutil.copytree(ROOT/folder,a.output/'source'/folder,ignore=shutil.ignore_patterns('__pycache__'))
 pipe=Pipeline(structural=not a.no_structural,ocr=not a.no_ocr);t=time.perf_counter()
 with pred.open('a') as f:
  for i,row in enumerate(rows):
   if row['sample_id'] in done:continue
   path=(DATASET_ROOT/row['path']).resolve()
   if not path.is_relative_to((DATASET_ROOT).resolve()):raise ValueError('Source outside dataset')
   queue_started=time.perf_counter()
   if a.mode=='hybrid':
    from .budget import Ledger
    with Ledger().connect() as c:
     latest=c.execute('SELECT time FROM attempts ORDER BY time DESC LIMIT 6').fetchall()
    if len(latest)==6:
     wait=max(0,61-(time.time()-latest[-1][0]))
     if wait>0:time.sleep(min(wait,61))
   queue_seconds=time.perf_counter()-queue_started
   r=pipe.answer(path,row['question'],row['sample_id'],mode=a.mode);r['timing']['cloud_rate_queue_seconds']=queue_seconds;r['path']=row['path'];f.write(json.dumps(r,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
   if (i+1)%20==0:print(json.dumps({'completed':i+1,'total':len(rows),'status':r['status'],'elapsed_seconds':time.perf_counter()-t}),flush=True)
 write_json(a.output/'complete.json',{'completed':len(rows),'seconds_this_process':time.perf_counter()-t,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'questions_sha256':sha(a.questions)})
if __name__=='__main__':main()
