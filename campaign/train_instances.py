import json,hashlib,time
from pathlib import Path
from qa.common import sha
from .clock import atomic,admit,now
from .instance_head import pool,fit,predict
from .review_run import scan
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 admit('optimize',300);folder=OUT/'instance-head';folder.mkdir(exist_ok=True);G={r['sample_id']:r for r in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};P=[json.loads(l)for l in(OUT/'candidate-ensemble/predictions.jsonl').open()];inv=json.loads((ROOT/'benchmarks/qa-v3/file-inventory.json').read_text());M=json.loads((OUT/'observations/manifest.json').read_text())['sources'];H={r['source_sha256']for r in M};rt=scan('cache/v2-rtdetr',H);custom={r['source_sha256']:json.loads((OUT/'observations/custom-yolo'/(r['key']+'.json')).read_text())for r in M};cubi={}
 for p in(ROOT/'cache/qa').glob('*.json'):
  r=json.loads(p.read_text());h=r.get('source_sha256')
  if h in H and r.get('preprocessing',{}).get('max_edge')==512:cubi.setdefault(h,r)
 review={}
 for p in(OUT/'reviews/gemini-3-flash-preview').glob('*.json'):
  if p.stem in H:review[p.stem]=json.loads(p.read_text())
 units={}
 for p in P:
  h=p.get('source_sha256');t=p.get('task',{}).get('target')
  if h in H and h in rt and t in['door','window']and not p['task'].get('filters')and p.get('input_kind')=='raster':units.setdefault((h,t),p)
 proposals={key:pool(rt[key[0]],custom[key[0]],review.get(key[0]),cubi.get(key[0]),key[1])for key in units};models={};oof={}
 atomic(folder/'manifest.json',{'time':now(),'parameters':{'steps':400,'l2':.015,'learning_rate':.025,'threshold':.5},'groups':len({inv[G[p['sample_id']]['path']]['group']for p in units.values()}),'source_only_features':True,'annotation_scope':'Only drawing-level count labels in training folds; no held-out/final labels','pipeline_source_sha256':sha(ROOT/'campaign/instance_head.py')})
 for cls in ['door','window']:
  keys=[k for k in units if k[1]==cls];fold=lambda k:int(hashlib.sha256(('selector-group-v1'+inv[G[units[k]['sample_id']]['path']]['group']).encode()).hexdigest()[:8],16)%5;models[cls]={}
  for f in range(5):
   admit('optimize',120);train=[k for k in keys if fold(k)!=f];m=fit([proposals[k]for k in train],[G[units[k]['sample_id']]['answer']for k in train]);models[cls][f]=m
   for k in keys:
    if fold(k)==f:oof[k]=predict(proposals[k],m)
   print('fit',cls,f,flush=True)
  atomic(folder/(cls+'.json'),fit([proposals[k]for k in keys],[G[units[k]['sample_id']]['answer']for k in keys]))
 result=[];base=[json.loads(l)for l in(OUT/'candidate-pdf-recovery-v3/predictions.jsonl').open()]
 for p in base:
  key=(p.get('source_sha256'),p.get('task',{}).get('target'))
  if key in oof and p.get('input_kind')=='raster'and not p['task'].get('filters'):
   e=oof[key];p=dict(p,answer=len(e),evidence=e,route='raster.weak-instance-consensus.campaign-v1',instance_head={'supervision':'drawing count only, out-of-fold grouped evaluation','feature_version':'weak-instance-consensus-v1'})
  result.append(p)
 (folder/'oof.predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in result));atomic(folder/'complete.json',{'time':now(),'units':len(units)})
if __name__=='__main__':main()
