"""Offline development calibration; references never imported by candidate adapter."""
import json,hashlib,collections,copy,time
from pathlib import Path
from .candidate import apply,TARGET_CLASSES
from .clock import atomic,admit,now
from .extraction import SHA
from evaluation.numeric import score
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
GRID={'confidence':[.25,.4,.55,.7],'iou':[.5,.7]}
def main():
 admit('optimize',15);atomic(OUT/'predefined-grid.json',{'time':now(),'grid':GRID,'group_split':'sha256(group_id) modulo4:0validation,1/2/3calibration; all translations together','selection':'Select per-target threshold on calibration; require validation gain before replacement; final full-development score is descriptive, not heldout','models':['frozen v3','existing custom YOLO11m']})
 gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};pred=[json.loads(l)for l in(ROOT/'results/v3/release-quick/predictions.jsonl').open()];man=json.loads((OUT/'observations/manifest.json').read_text());observations={}
 for r in man['sources']:
  p=OUT/'observations/custom-yolo'/(r['key']+'.json')
  if p.exists():observations[r['source_sha256']]=json.loads(p.read_text())
 rows=[p for p in pred if p.get('input_kind')=='raster'and p.get('task',{}).get('target')in TARGET_CLASSES and p.get('source_sha256')in observations];target_report={};config={'version':'overnight-specialist-router-v1','custom_weight_sha256':SHA,'targets':{}}
 for target in TARGET_CLASSES:
  sample=[p for p in rows if p['task']['target']==target and not p['task'].get('filters')];fold=lambda p:'validation'if int(hashlib.sha256(gold[p['sample_id']]['group_id'].encode()).hexdigest()[:8],16)%4==0 else'calibration';base={f:sum(score(gold[p['sample_id']],p)['passed']is True for p in sample if fold(p)==f)for f in ['calibration','validation']};n={f:sum(fold(p)==f for p in sample)for f in base};settings=[]
  for conf in GRID['confidence']:
   for iou in GRID['iou']:
    cfg=dict(config,targets={target:{'confidence':conf,'iou':iou}});counts={f:0 for f in base}
    for p in sample:
     r=apply(p,observations[p['source_sha256']],cfg);counts[fold(p)]+=score(gold[p['sample_id']],r)['passed']is True
    settings.append({'confidence':conf,'iou':iou,'correct':counts})
  best=max(settings,key=lambda s:(s['correct']['calibration'],-abs(s['confidence']-.4),s['iou']))
  # Validation must improve and calibration may not worsen. Small samples do not promote.
  promote=n['validation']>=20 and best['correct']['validation']>base['validation']and best['correct']['calibration']>=base['calibration']
  if promote:config['targets'][target]={'confidence':best['confidence'],'iou':best['iou']}
  target_report[target]={'n':n,'baseline':base,'settings':settings,'best':best,'promoted_in_candidate':promote}
 atomic(OUT/'calibration.json',{'time':now(),'targets':target_report,'observation_sources':len(observations)});atomic(OUT/'candidate-config.json',config)
 result=[]
 for p in pred:
  obs=observations.get(p.get('source_sha256'));r=apply(p,obs,config)if obs else p;result.append(r)
 folder=OUT/'candidate-local';folder.mkdir(exist_ok=True);temp=folder/'predictions.jsonl.tmp';temp.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in result));temp.replace(folder/'predictions.jsonl')
 correct=sum(score(gold[p['sample_id']],p)['passed']is True for p in result);atomic(folder/'summary.json',{'total':len(result),'valid_references':9471,'correct':correct,'primary':correct/9471,'correct_all':correct/9544,'observation_sources':len(observations),'targets':config['targets'],'note':'Development calibration and final full-dev descriptive score; validation not untouched final evaluation'})
 print(json.dumps(target_report));print('FULL-DEV',correct,'/9471',correct/9471)
if __name__=='__main__':main()
