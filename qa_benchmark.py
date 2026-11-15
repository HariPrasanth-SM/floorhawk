"""Checkpointed inference only. Accepts exactly sample_id/path/question fields."""
import argparse,json,time,shutil,resource
from pathlib import Path
from qa.common import ROOT,sha,versions,write_json
from qa.pipeline import Pipeline

def main():
 p=argparse.ArgumentParser();p.add_argument('--questions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--data-root',type=Path,default=ROOT.parent/'datasets/junction-dataset');p.add_argument('--device',choices=['cpu','0'],default='cpu');p.add_argument('--max-edge',type=int,default=512);p.add_argument('--vlm-url');p.add_argument('--resume',action='store_true');a=p.parse_args()
 rows=[json.loads(l) for l in a.questions.open() if l.strip()]
 if any(set(r)!={'sample_id','path','question'} for r in rows):raise ValueError('Inference input must contain ONLY sample_id, path and question')
 if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('Duplicate sample IDs')
 a.output.mkdir(parents=True,exist_ok=a.resume);predpath=a.output/'predictions.jsonl';metadata={'questions_sha256':sha(a.questions),'device':a.device,'max_edge':a.max_edge,'vlm_url':a.vlm_url}
 pipeline=Pipeline(a.device,a.max_edge,a.vlm_url);metadata['pipeline_sources']=pipeline.sources
 done=set()
 if a.resume:
  previous=json.loads((a.output/'run.json').read_text())
  if previous['settings']!=metadata:raise ValueError('Resume settings/source mismatch; use a new output')
  if predpath.exists():
   # A crash may leave an unterminated final line. Preserve it separately, then resume complete records.
   lines=predpath.read_text().splitlines();valid=[]
   for index,line in enumerate(lines):
    try:r=json.loads(line)
    except json.JSONDecodeError:
     if index!=len(lines)-1:raise
     (a.output/'interrupted-tail.txt').write_text(line);continue
    valid.append(line);done.add(r['sample_id'])
   if len(valid)!=len(done):raise ValueError('Duplicate saved sample IDs')
   if len(valid)!=len(lines):predpath.write_text('\n'.join(valid)+'\n')
 else:
  write_json(a.output/'run.json',{'settings':metadata,'dependencies':versions(),'started':time.time(),'row_count':len(rows)})
  source=a.output/'source';source.mkdir();shutil.copytree(ROOT/'qa',source/'qa',ignore=shutil.ignore_patterns('__pycache__'));shutil.copy2(ROOT/'qa_benchmark.py',source/'qa_benchmark.py')
 if not done.issubset({r['sample_id'] for r in rows}):raise ValueError('Saved predictions contain unknown sample IDs')
 if len(done)==len(rows) and (a.output/'complete.json').exists():
  print('Already complete; preserved all outputs and original timing metadata.');return
 started=time.perf_counter();n=0
 with predpath.open('a') as dest:
  for row in rows:
   if row['sample_id'] in done:continue
   path=(a.data_root/row['path']).resolve()
   if not path.is_relative_to(a.data_root.resolve()):raise ValueError('Unsafe manifest path')
   result=pipeline.answer(path,row['question'],row['sample_id']);result['path']=row['path'];dest.write(json.dumps(result,ensure_ascii=False)+'\n');dest.flush();n+=1
   if n%200==0 or len(rows)<110:print(json.dumps({'completed':len(done)+n,'total':len(rows),'status':result['status'],'route':result['route'],'last_seconds':result['latency_seconds'],'elapsed_seconds':time.perf_counter()-started}),flush=True)
 write_json(a.output/'complete.json',{'rows':len(rows),'completed':len(done)+n,'seconds_this_process':time.perf_counter()-started,'questions_sha256':sha(a.questions),'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
if __name__=='__main__':main()
