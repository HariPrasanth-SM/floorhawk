"""Grouped development selector for real opening-proposal alternatives only."""
import json,hashlib,collections,time,copy,argparse
from pathlib import Path
import numpy as np
from .clock import atomic,admit,now
from .learn import train
from .selector import proposals,rank
from .openings import candidates,features,FEATURE_NAMES
from .review_run import scan
from qa.common import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
PARAMETERS={'depth':2,'trees':64,'learning_rate':.1,'lambda':5.,'minimum_leaf':24,'quantile_splits':9}
from .openings import choose

def main():
 p=argparse.ArgumentParser();p.add_argument('--tag',default='opening-selector');p.add_argument('--depth',type=int,choices=[2,3],default=2);p.add_argument('--trees',type=int,choices=[64,100],default=64);p.add_argument('--leaf',type=int,choices=[16,24],default=24);args=p.parse_args();PARAMETERS.update(depth=args.depth,trees=args.trees,minimum_leaf=args.leaf)
 if not args.tag.replace('-','').isalnum():raise ValueError('Invalid result tag')
 admit('optimize',240);folder=OUT/args.tag
 if(folder/'complete.json').exists():raise ValueError('Completed experiment is immutable; select a new tag')
 folder.mkdir(exist_ok=True);gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};ps=[json.loads(l)for l in(OUT/'candidate-ensemble/predictions.jsonl').open()];inv=json.loads((ROOT/'benchmarks/qa-v3/file-inventory.json').read_text());m=json.loads((OUT/'observations/manifest.json').read_text())['sources'];H={r['source_sha256']for r in m};rt=scan('cache/v2-rtdetr',H);words=scan('cache/v2-ocr',H);custom={r['source_sha256']:json.loads((OUT/'observations/custom-yolo'/(r['key']+'.json')).read_text())for r in m};review={}
 for p in(OUT/'reviews/gemini-3-flash-preview').glob('*.json'):
  if p.stem in H:
   r=json.loads(p.read_text())
   if r.get('status')=='success':review[p.stem]=r
 units={}
 for p in ps:
  h=p.get('source_sha256');target=p.get('task',{}).get('target')
  if h in H and h in rt and target in ['door','window']and not p['task'].get('filters')and p.get('input_kind')=='raster':units.setdefault((h,target),p)
 examples=[]
 for(h,target),p in units.items():
  g=gold[p['sample_id']];group=inv[g['path']]['group'];fold=int(hashlib.sha256(('selector-group-v1'+group).encode()).hexdigest()[:8],16)%5;size=inv[g['path']]['size'];wr=words.get(h,{}).get('words',[])
  for source,r in proposals(p,review.get(h),wr)+candidates(p,rt[h],custom[h],review.get(h)):
   x=features(p,r,source,review.get(h),wr,size,rt[h],custom[h]);assert len(x)==len(FEATURE_NAMES);examples.append({'x':x,'y':int(r['answer']==g['answer']),'fold':fold,'group':group,'target':target})
 X=np.asarray([e['x']for e in examples]);y=np.asarray([e['y']for e in examples]);models={};atomic(folder/'manifest.json',{'time':now(),'parameters':PARAMETERS,'examples':len(examples),'units':len(units),'groups':len({e['group']for e in examples}),'features':FEATURE_NAMES,'grouped_folds':5,'inference_never_reads_gold':True})
 for fold in range(5):
  admit('optimize',120);ids=[i for i,e in enumerate(examples)if e['fold']!=fold];t=time.monotonic();model=train(X[ids],y[ids],PARAMETERS);model['features']=FEATURE_NAMES;model['version']='opening-proposal-selector-v1';models[fold]=model;atomic(folder/f'fold-{fold}.json',model);print('fold',fold,time.monotonic()-t,flush=True)
 semantic={r['sample_id']:r for r in(json.loads(l)for l in(OUT/'selector-full361/oof.predictions.jsonl').open())};result=[]
 for p in ps:
  h=p.get('source_sha256');target=p.get('task',{}).get('target')
  if(h,target)in units and not p['task'].get('filters')and p.get('input_kind')=='raster':
   g=gold[p['sample_id']];group=inv[g['path']]['group'];fold=int(hashlib.sha256(('selector-group-v1'+group).encode()).hexdigest()[:8],16)%5;r=choose(p,review.get(h),words.get(h,{}).get('words',[]),inv[g['path']]['size'],rt[h],custom[h],models[fold]);r['opening_selector']['evaluation_fold']=fold
  else:r=semantic[p['sample_id']]
  result.append(r)
 (folder/'oof.predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in result));model=train(X,y,PARAMETERS);model['features']=FEATURE_NAMES;model['version']='opening-proposal-selector-v1';atomic(folder/'model.json',model);atomic(folder/'complete.json',{'time':now(),'model_sha256':sha(folder/'model.json'),'examples':len(examples)});print('complete',len(examples),flush=True)
if __name__=='__main__':main()
