from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Answer-free, checkpointed version3 runner. Cloud batch remains frozen40 only."""
import argparse,json,time,os,shutil,resource
from pathlib import Path
from qa.common import ROOT,sha,write_json,versions
from .pipeline import Pipeline

def main():
 p=argparse.ArgumentParser();p.add_argument('--questions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['local','hybrid'],default='local');p.add_argument('--resume',action='store_true');a=p.parse_args();rows=[json.loads(l) for l in a.questions.open()]
 if any(set(r)!={'sample_id','path','question'} for r in rows):raise ValueError('Only question/sample identity fields accepted')
 if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('Duplicate question IDs')
 if a.mode=='hybrid' and (len(rows)>40 or sha(a.questions)!=sha(ROOT/'benchmarks/v2/paired.questions.jsonl')):raise ValueError('Expanded batch cloud authorization pending; only frozen40 allowed')
 sources={str(f.relative_to(ROOT)):sha(f) for folder in ['v3','v2','qa'] for f in sorted((ROOT/folder).glob('*.py'))};settings={'questions_sha256':sha(a.questions),'mode':a.mode,'sources':sources,'adapter_config_sha256':sha(ROOT/'v3/adapter-config.json'),'config_sha256':sha(ROOT/'v3/config.json')}
 if a.questions.resolve()==(RESULTS_ROOT/'v3/reserved50/questions.jsonl').resolve():
  freeze=RESULTS_ROOT/'v3/freeze.json'
  if not freeze.exists():raise ValueError('Freeze source/model settings before reserved inference')
  frozen=json.loads(freeze.read_text())
  if frozen['pipeline_sources']!=sources or frozen['config_sha256']!=settings['config_sha256'] or frozen['adapter_config_sha256']!=settings['adapter_config_sha256']:raise ValueError('Reserved inference must use the frozen source/configuration')
  if (RESULTS_ROOT/'v3/reserved50/SCORED_ONCE.json').exists():raise ValueError('Reserved answers already opened; do not rerun/tune on this probe')
  settings['freeze_sha256']=sha(freeze)
 a.output.mkdir(parents=True,exist_ok=a.resume);pred=a.output/'predictions.jsonl';done=set()
 if a.resume:
  if json.loads((a.output/'run.json').read_text())['settings']!=settings:raise ValueError('Source/settings changed; choose a fresh output')
  if pred.exists():
   lines=pred.read_text().splitlines();valid=[]
   for i,line in enumerate(lines):
    try:record=json.loads(line)
    except json.JSONDecodeError:
     if i!=len(lines)-1:raise
     (a.output/'interrupted-tail.txt').write_text(line);continue
    done.add(record['sample_id']);valid.append(line)
   if len(valid)!=len(lines):pred.write_text('\n'.join(valid)+'\n')
  if len(done)==len(rows) and (a.output/'complete.json').exists():print('Already complete; original timing/results preserved.');return
 else:
  write_json(a.output/'run.json',{'settings':settings,'dependencies':versions(),'started':time.time(),'n':len(rows),'role':'development; not heldout','cache_policy':'original generation times retained separately; repeated queries reuse drawing facts'})
  for folder in ['v3','v2','qa']:shutil.copytree(ROOT/folder,a.output/'source'/folder,ignore=shutil.ignore_patterns('__pycache__'))
 pipe=Pipeline();started=time.perf_counter()
 with pred.open('a') as f:
  for i,row in enumerate(rows):
   if row['sample_id'] in done:continue
   path=(DATASET_ROOT/row['path']).resolve()
   if not path.is_relative_to((DATASET_ROOT).resolve()):raise ValueError('Path outside dataset')
   if a.mode=='hybrid':
    from v2.budget import Ledger
    with Ledger().connect() as c:latest=c.execute('SELECT time FROM attempts ORDER BY time DESC LIMIT 6').fetchall()
    if len(latest)==6:
     wait=max(0,61-(time.time()-latest[-1][0]))
     if wait:time.sleep(min(wait,61))
   r=pipe.answer(path,row['question'],row['sample_id'],mode=a.mode);r['path']=row['path'];f.write(json.dumps(r,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
   if (i+1)%50==0:print(i+1,len(rows),round(time.perf_counter()-started,2),flush=True)
 write_json(a.output/'complete.json',{'completed':len(rows),'seconds_this_process':time.perf_counter()-started,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
if __name__=='__main__':main()
