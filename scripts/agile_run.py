"""One-hour bounded candidate inference; no evaluator/reference import."""
import sys,os,json,time,copy,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT,DATASET_ROOT
from v2.budget import Ledger
O=RESULTS_ROOT/'agile1/experiment'
def main():
 from demo_gpu import install
 from v3.pipeline import Pipeline
 from iteration.paired import Engine
 from custom_detector import answer as custom_answer
 from cumulative_evidence import decision
 from v2.supervisor import fresh_host,Admission
 stop=json.loads((RESULTS_ROOT/'agile1/authorization.json').read_text())['experiment_stop_epoch'];before=Ledger().summary();write_json(O/'budget-before.json',before)
 qfile=O/'questions.jsonl';qs=[json.loads(l)for l in qfile.open()];assert len(qs)==32 and all(set(q)==set(['sample_id','path','question'])for q in qs)
 if(O/'local.predictions.jsonl').exists():raise RuntimeError('Existing run preserved; no silent overwrite')
 install();pipeline=Pipeline('cpu',512);pipeline.set_cloud(False);pipeline.local_routing=False;engine=Engine(pipeline,cumulative=True);engine.pipeline.cloud_enabled=False;local=[];custom=[];started=time.perf_counter()
 with(O/'local.predictions.jsonl').open('x')as out,(O/'custom.predictions.jsonl').open('x')as custom_out:
  for q in sorted(qs,key=lambda q:(q['path'],q['sample_id'])):
   if time.time()>stop-300:break
   if Admission().check(fresh_host())!='admit':raise RuntimeError('Resource admission paused; partials retained')
   t=time.perf_counter();r=engine.local(DATASET_ROOT/q['path'],q['question'],q['sample_id']);r.update(path=q['path'],sample_id=q['sample_id'],question=q['question']);out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush();local.append(r)
   alt=copy.deepcopy(r);target=r.get('task',{}).get('target');items=[e for e in r.get('cumulative_evidence',{}).get('evidence',[])if e.get('origin_model')=='custom_yolo']
   if r.get('task',{}).get('operation')=='count'and Path(q['path']).suffix.lower()=='.png':
    if target=='shower_bath':selected=[e for e in items if e['class']in['shower','bathtub']]
    else:selected=[e for e in items if e.get('class')==target]
    available=any(o.get('model')=='custom_yolo'and o.get('status')=='available'for o in r.get('cumulative_evidence',{}).get('outputs',[]))
    alt.update(status='success'if available else'unsupported',answer=len(selected)if available else None,unit='count',evidence=selected,route='raster.custom_yolo.candidate')
   alt['candidate_note']='Custom YOLO for supported PNG targets; unchanged native routes otherwise. No best-of-gold selection.';custom_out.write(json.dumps(alt,ensure_ascii=False)+'\n');custom_out.flush();custom.append(alt);print('Local',q['sample_id'],r['status'],r.get('answer'),'custom',alt.get('answer'),round(time.perf_counter()-t,3),flush=True)
 write_json(O/'local-complete.json',{'n':len(local),'seconds':time.perf_counter()-started,'local_source_config':engine.config,'configuration_sha256':engine.config_sha256,'question_sha256':sha(qfile)})
 engine.close()
 write_json(O/'run-local-only.json', {'n_local':len(local), 'n_custom':len(custom), 'cloud_disabled':'Current AGENTS.md requires local-only inference'})
 return
if __name__=='__main__':main()
