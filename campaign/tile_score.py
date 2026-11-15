"""Offline bounded tile proposal comparison; complete coverage only."""
import json,collections,hashlib
from pathlib import Path
from .clock import atomic,now
from .review_run import scan
from v3.dedup import overlap
from evaluation.numeric import score
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
PROFILES={f'{mode}-{conf}':{'mode':mode,'confidence':conf}for mode in ['tile','union']for conf in [.5,.65,.8]}
def merge(rows,cls,conf):
 result=[]
 for e in sorted([r for r in rows if r['class']==cls and r.get('score',0)>=conf],key=lambda r:(r.get('score',0),not r.get('internal_border_fragment')),reverse=True):
  if not any(overlap(e['bbox'],k['bbox'])[0]>.5 or overlap(e['bbox'],k['bbox'])[1]>.85 for k in result):result.append(e)
 return result
def main():
 gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};pred=[json.loads(l)for l in(OUT/'candidate-ensemble/predictions.jsonl').open()];obs={}
 for p in(OUT/'observations/rtdetr-tiles').glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('status')=='success'and r.get('coverage',{}).get('complete'):obs[r['source_sha256']]=r
 rt=scan('cache/v2-rtdetr',set(obs));report={};policy={}
 for cls in ['door','window']:
  ps=[p for p in pred if p.get('source_sha256')in obs and p.get('task',{}).get('target')==cls and not p['task'].get('filters')];fold=lambda p:'validation'if int(hashlib.sha256(gold[p['sample_id']]['group_id'].encode()).hexdigest()[:8],16)%4==0 else'calibration';baseline={f:sum(score(gold[p['sample_id']],p)['passed']is True for p in ps if fold(p)==f)for f in ['calibration','validation']};settings={}
  for name,cfg in PROFILES.items():
   counts={f:0 for f in baseline}
   for p in ps:
    h=p['source_sha256'];raw=obs[h]['entities']+(rt.get(h,{}).get('entities',[])if cfg['mode']=='union'else[]);e=merge(raw,cls,cfg['confidence']);r=dict(p,answer=len(e),status='success');counts[fold(p)]+=score(gold[p['sample_id']],r)['passed']is True
   settings[name]=counts
  best=max(settings,key=lambda k:settings[k]['calibration']);v_n=sum(fold(p)=='validation'for p in ps);promote=v_n>=20 and settings[best]['calibration']>baseline['calibration']and settings[best]['validation']>baseline['validation'];report[cls]={'n':len(ps),'baseline':baseline,'profiles':settings,'best':best,'validation_n':v_n,'promote':promote}
  if promote:policy[cls]=PROFILES[best]
 atomic(OUT/'tile-calibration.json',{'time':now(),'sources':len(obs),'predefined_profiles':PROFILES,'report':report,'policy':policy});print(json.dumps({'sources':len(obs),'report':report}))
if __name__=='__main__':main()
