import json,hashlib,collections
from pathlib import Path
from qa.common import sha
from evaluation.numeric import score
from .ensemble import instances,PROFILES
from .review_run import scan
from .clock import atomic,now
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};pred=[json.loads(l)for l in(OUT/'candidate-local/predictions.jsonl').open()];m=json.loads((OUT/'observations/manifest.json').read_text())['sources'];hashes={r['source_sha256']for r in m};rt=scan('cache/v2-rtdetr',hashes);custom={r['source_sha256']:json.loads((OUT/'observations/custom-yolo'/(r['key']+'.json')).read_text())for r in m};report={};policy={}
 for target in ['door','window']:
  ps=[p for p in pred if p.get('input_kind')=='raster'and p.get('task',{}).get('target')==target and not p['task'].get('filters')and p.get('source_sha256')in rt and custom.get(p.get('source_sha256'),{}).get('status')=='success'];fold=lambda p:'validation'if int(hashlib.sha256(gold[p['sample_id']]['group_id'].encode()).hexdigest()[:8],16)%4==0 else'calibration';base={f:sum(score(gold[p['sample_id']],p)['passed']is True for p in ps if fold(p)==f)for f in ['calibration','validation']};scores={}
  for profile in PROFILES:
   counts={f:0 for f in base}
   for p in ps:
    h=p['source_sha256'];entities=instances(rt[h]['entities'],custom[h]['entities'],target,profile);r=dict(p,answer=len(entities),status='success');counts[fold(p)]+=score(gold[p['sample_id']],r)['passed']is True
   scores[profile]=counts
  best=max(scores,key=lambda k:scores[k]['calibration']);promote=scores[best]['calibration']>base['calibration']and scores[best]['validation']>base['validation'];report[target]={'n':len(ps),'baseline':base,'profiles':scores,'selected':best,'promote':promote}
  if promote:policy[target]=best
 result=[]
 for p in pred:
  target=p.get('task',{}).get('target');h=p.get('source_sha256')
  if target in policy and h in rt and custom.get(h,{}).get('status')=='success' and p.get('input_kind')=='raster'and not p['task'].get('filters'):
   e=instances(rt[h]['entities'],custom[h]['entities'],target,policy[target]);p=dict(p,answer=len(e),evidence=e,route='raster.instance-corroboration.campaign-v1',postprocessing={'profile':policy[target],'selection':'drawing-group development validation','raw_rtdetr_model':rt[h]['model'],'custom_model':custom[h]['model']},calculation_trace=[{'operation':'count_unique_included_entities','ids':[e['id']for e in e],'value':len(e)}])
  result.append(p)
 atomic(OUT/'ensemble-calibration.json',{'time':now(),'profiles':PROFILES,'targets':report,'policy':policy});folder=OUT/'candidate-ensemble';folder.mkdir(exist_ok=True);(folder/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in result));print(json.dumps(report))
if __name__=='__main__':main()
