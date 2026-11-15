"""Six frozen exploratory questions, no reference answers, <=12 new HTTP attempts."""
import sys,json,time,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import DATASET_ROOT,RESULTS_ROOT
from v2.budget import Ledger
from v2.supervisor import Admission,fresh_host
from large_drawing import LargeDrawing
O=Path(os.environ.get('PROOFPLAN_SAMPLES_RUN',str(RESULTS_ROOT/'samples25')));O.mkdir(parents=True,exist_ok=True);START=1794668850;DEADLINE=1794670350
QUESTIONS=[('us_daf_dorm_sd_drawings_april_2026_p003.png','How many windows are shown on this floor plan?'),('us_daf_dorm_sd_drawings_april_2026_p003.png','Identify a clearly labelled space or wing and report its printed floor area, if present. Do not present a wing total as an individual room area.'),('us_aw_078-24-28_march_2020_p096.png','What diameter is explicitly specified for the suction header? Cite its printed label; abstain if unreadable.'),('us_aw_078-24-28_march_2020_p096.png','Which explicitly labelled pump or equipment types are present? Cite their labels; do not claim a complete equipment inventory.'),('us_aw_078-24-33_p056.png','What slab thickness and reinforcement specifications are explicitly noted? Cite source labels and do not invent construction rules.'),('us_aw_078-24-33_p056.png','Which annotated region does one selected slab specification refer to? If its area cannot be established reliably, explain the missing information. A printed scale alone does not calibrate this raster.')]
def main():
 from datetime import datetime,timedelta
 started=datetime.fromisoformat('2026-11-14T15:07:30+00:00').timestamp();stop=started+18*60
 from demo_gpu import install
 from v3.pipeline import Pipeline
 from iteration.paired import Engine
 if(O/'predictions.jsonl').exists():raise RuntimeError('Preserve prior smoke run')
 write_json(O/'questions.json',[{'id':f'exploratory-{i+1}','source':name,'question':q,'scope':'supplied sheet only, unscored'}for i,(name,q)in enumerate(QUESTIONS)])
 before=Ledger().summary();write_json(O/'budget-before.json',before);install();engine=Engine(Pipeline('cpu',512));large=LargeDrawing(engine);results=[]
 with(O/'predictions.jsonl').open('x')as out:
  for i in [0,2,4,1,3,5]:
   name,q=QUESTIONS[i]
   if time.time()>stop-100:break
   b=Ledger().summary()
   if b['requests_reserved']-before['requests_reserved']>10 or b['estimated_usd_max']-b['estimated_usd_reserved']<.024:break
   if Admission().check(fresh_host())!='admit':break
   t=time.perf_counter();source=DATASET_ROOT.parent/'samples'/name
   try:r=large.answer(source,q,mode='hybrid');r.update(id=f'exploratory-{i+1}',source_name=name,question=q,scope='supplied sheet only; unscored exploratory development',elapsed_seconds=time.perf_counter()-t)
   except Exception as e:r={'id':f'exploratory-{i+1}','source_name':name,'question':q,'status':'execution_error','error':type(e).__name__+': '+str(e)[:200]}
   out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush();results.append(r);print(r['id'],r['status'],r.get('coverage',{}).get('processed_tiles'),r.get('paired',{}).get('hybrid',{}).get('status'),flush=True)
 engine.close();after=Ledger().summary();write_json(O/'run.json',{'n':len(results),'unscored':True,'before':before,'after':after,'attempts':after['requests_reserved']-before['requests_reserved'],'reserved_usd':after['estimated_usd_reserved']-before['estimated_usd_reserved'],'question_sha256':sha(O/'questions.json'),'predictions_sha256':sha(O/'predictions.jsonl'),'untested':[f'exploratory-{i+1}'for i in range(6)if f'exploratory-{i+1}'not in{r['id']for r in results}]})
if __name__=='__main__':main()
