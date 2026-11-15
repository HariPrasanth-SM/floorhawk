"""Apply general PDF evidence improvements; no reference-dependent routing."""
import json,copy
from pathlib import Path
from qa.tools import pdf_answer
from .clock import atomic,now
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 ps=[json.loads(l)for l in(OUT/'opening-selector/oof.predictions.jsonl').open()];area={};doors={}
 for p in(OUT/'observations/pdf-prefixed-v3').glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('status')=='success':area[r['source_sha256']]=r['facts']
 for p in(OUT/'observations/pdf-doors').glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('status')=='success':doors[r['source_sha256']]=r
 output=[];area_applied=0;door_applied=0
 for p in ps:
  h=p.get('source_sha256');task=p.get('task',{})
  if h in area:
   from qa.router import route
   task=route(p['question'])
  if h in area and p['status']!='success'and task.get('operation')in['area','count']and task.get('target')in['room','apartment']and task.get('scope')!='model':
   r=pdf_answer(area[h],task,p['question'])
   if r['status']=='success':p=copy.deepcopy(p);p['previous_local']={k:copy.deepcopy(p.get(k))for k in ['status','answer','route','evidence']};p.update(r,task=task,route='pdf.prefixed-native-room-evidence.campaign-v3',closed_room_geometry_recovery=area[h]['closed_room_geometry_recovery']);area_applied+=1
  output.append(p)
 folder=OUT/'candidate-pdf-recovery-v3';folder.mkdir(exist_ok=True);(folder/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in output));atomic(folder/'manifest.json',{'time':now(),'area_sources':len(area),'area_recovered_answers':area_applied,'door_candidates_not_promoted_yet':len(doors),'note':'All original successes retained; missing areas require native closed polygon and explicit printed physical PDF scale. No answer source lookup.'});print('Recovered',area_applied,'from',len(area),'PDFsources')
if __name__=='__main__':main()
