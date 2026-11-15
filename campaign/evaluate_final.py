"""Checkpointed, question-only frozen Local evaluation after verified delivery.

References are deliberately absent. Grade in a separate process after inference.
"""
import argparse,json,time,hashlib,base64,collections,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.environ['PROOFPLAN_CACHE_ROOT']=str(ROOT/'results/overnight-20261115/final-local/cache')
import modal
from campaign.clock import admit,DEADLINES,atomic,now
from campaign.final_contract import validate_questions
from runtime_paths import DATASET_ROOT
from qa.common import sha
OUT=ROOT/'results/overnight-20261115'
def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--limit-sources',type=int,default=1000);p.add_argument('--backend',choices=['cpu','modal'],default='cpu');a=p.parse_args()
 if not(OUT/'FROZEN.json').is_file():raise RuntimeError('Optimization not frozen')
 delivery=json.loads((OUT/'DELIVERY_VERIFIED.json').read_text())
 if not delivery.get('passed')or delivery.get('source_commit')!=a.release:raise RuntimeError('Matching deployment/submission delivery not verified')
 admit('evaluate',130);dest=OUT/'final-local';dest.mkdir(exist_ok=True);manifest=json.loads((OUT/'final-eligibility/manifest.json').read_text());groups=collections.OrderedDict()
 for name in ['known-unexposed.questions.jsonl','unknown-custom-overlap.questions.jsonl']:
  path=OUT/'final-eligibility'/name
  if sha(path)!=manifest['files'][name]:raise ValueError('Frozen eligibility manifest changed')
  for q in(json.loads(l)for l in path.open()):groups.setdefault(q['path'],[]).append(q)
 if a.backend=='modal':worker=modal.Cls.from_name('floorhawk-final-evaluation','FinalWorker')();execute=worker.evaluate.remote
 else:
  from campaign.cpu_final import CPUFinal
  worker=CPUFinal(a.release);execute=worker.evaluate
 completed=0
 for path,questions in groups.items():
  admit('evaluate',130)
  if completed>=a.limit_sources:break
  source=DATASET_ROOT/path;h=sha(source);file=dest/'sources'/(h+'.json');previous=json.loads(file.read_text())if file.exists()else None
  if previous and previous['source_commit']!=a.release:raise ValueError('Do not mix frozen source versions')
  seen={r['sample_id']for r in previous.get('rows',[])}if previous else set();remaining=[q for q in questions if q['sample_id']not in seen]
  if not remaining:continue
  result_rows=previous.get('rows',[])if previous else[];calls=previous.get('source_calls',[])if previous else[]
  for start in range(0,len(remaining),128):
   admit('evaluate',130);batch=remaining[start:start+128];payload=[{'sample_id':q['sample_id'],'question':q['question']}for q in batch];validate_questions(payload);before=time.monotonic()
   try:result=execute(h,source.suffix.lower(),base64.b64encode(source.read_bytes()).decode(),payload,a.release,DEADLINES['evaluate'])
   except Exception as exc:
    atomic(dest/'last-error.json',{'time':now(),'source_sha256':h,'exception_type':type(exc).__name__,'note':'No fake predictions; retained completed source checkpoints'});raise
   assert result['source_sha256']==h and result['source_commit']==a.release;lookup={q['sample_id']:q for q in batch}
   for row in result['rows']:
    if row['sample_id']not in lookup:raise ValueError('Unrequested result identity')
    row.update(path=path);result_rows.append(row)
   for observation in result.pop('observations',[]):
    rel=Path(observation['relative_path'])
    if rel.is_absolute()or'..'in rel.parts:raise ValueError('Invalid observation path')
    raw=observation['json_text'].encode();assert hashlib.sha256(raw).hexdigest()==observation['sha256'];target=dest/'observations'/h/rel;target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_suffix(target.suffix+'.tmp');temp.write_bytes(raw);temp.replace(target)
   calls.append({'source_seconds':result['source_seconds'],'remote_roundtrip_seconds':time.monotonic()-before,'resident':result['resident'],'questions':len(result['rows']),'provider_attempts':0});atomic(file,{'source_sha256':h,'source_commit':a.release,'path':path,'rows':result_rows,'source_calls':calls,'complete':len({r['sample_id']for r in result_rows})==len(questions)})
   print(json.dumps({'source_sha256':h,'questions':len(result_rows),'expected':len(questions),'seconds':calls[-1]['remote_roundtrip_seconds']}),flush=True)
  completed+=1
  all_rows=[r for f in(dest/'sources').glob('*.json')for r in json.loads(f.read_text())['rows']];atomic(dest/'progress.json',{'time':now(),'source_commit':a.release,'sources':len(list((dest/'sources').glob('*.json'))),'recorded_questions':len(all_rows),'eligible_questions':manifest['eligible_questions'],'provider_attempts':0,'mode':'Frozen Local only; no model/provider tuning based on final results'});temp=dest/'predictions.jsonl.tmp';temp.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in all_rows));temp.replace(dest/'predictions.jsonl')
 atomic(dest/'complete.json',{'time':now(),'source_commit':a.release,'provider_attempts':0,'note':'Only source checkpoints define completed coverage; inspect progress before claiming full completion'})
if __name__=='__main__':main()
