"""Bounded logistic tree boosting and drawing-group CV for proposal selection.
Only this evaluator/trainer reads references; deployment imports selector.py only.
"""
import json,hashlib,collections,time,math,argparse,copy
from pathlib import Path
import numpy as np
from qa.common import sha
from .selector import proposals,features,rank,select,VERSION,FEATURE_NAMES
from .review_run import scan
from .clock import atomic,admit,now
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
PARAMETERS={'depth':2,'trees':48,'learning_rate':.10,'lambda':3.0,'minimum_leaf':16,'quantile_splits':9}
def train(X,y,parameters=PARAMETERS):
 X=np.asarray(X,dtype=np.float64);y=np.asarray(y,dtype=np.float64);prior=float(np.clip(y.mean(),.01,.99));intercept=math.log(prior/(1-prior));z=np.full(len(y),intercept);splits=[np.unique(np.quantile(X[:,j],np.linspace(.05,.95,parameters['quantile_splits'])))for j in range(X.shape[1])];trees=[]
 for iteration in range(parameters['trees']):
  p=1/(1+np.exp(-np.clip(z,-35,35)));gradient=y-p;hessian=np.maximum(p*(1-p),1e-3)
  def grow(ids,depth):
   G=gradient[ids].sum();H=hessian[ids].sum();leaf=float(np.clip(G/(H+parameters['lambda']),-2,2));best=None;gain=0;parent=G*G/(H+parameters['lambda'])
   if depth>=parameters['depth']or len(ids)<2*parameters['minimum_leaf']:return {'leaf':leaf}
   for j,thresholds in enumerate(splits):
    vals=X[ids,j]
    for threshold in thresholds:
     mask=vals<=threshold;n=int(mask.sum())
     if n<parameters['minimum_leaf']or len(ids)-n<parameters['minimum_leaf']:continue
     gl=gradient[ids[mask]].sum();hl=hessian[ids[mask]].sum();improvement=gl*gl/(hl+parameters['lambda'])+(G-gl)**2/(H-hl+parameters['lambda'])-parent
     if improvement>gain+1e-9:gain=improvement;best=(j,float(threshold),ids[mask],ids[~mask])
   if best is None:return {'leaf':leaf}
   j,t,left,right=best;return {'feature':j,'threshold':t,'left':grow(left,depth+1),'right':grow(right,depth+1)}
  tree=grow(np.arange(len(y)),0);trees.append(tree)
  from .selector import tree_value
  z+=parameters['learning_rate']*np.asarray([tree_value(tree,x)for x in X])
 return {'version':VERSION,'features':FEATURE_NAMES,'intercept':intercept,'learning_rate':parameters['learning_rate'],'trees':trees,'parameters':parameters,'score_kind':'uncalibrated proposal-ranking score, never confidence in completeness'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--tag',default='selector-complete');a=p.parse_args();admit('optimize',120);folder=OUT/a.tag;folder.mkdir(exist_ok=True)
 gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};pred=[json.loads(l)for l in(OUT/'candidate-ensemble/predictions.jsonl').open()];inv=json.loads((ROOT/'benchmarks/qa-v3/file-inventory.json').read_text());manifest=json.loads((OUT/'observations/manifest.json').read_text())['sources'];hashes={r['source_sha256']for r in manifest};sizes={r['source_sha256']:inv[r['path']]['size']for r in manifest};words=scan('cache/v2-ocr',hashes);reviews={}
 for p in(OUT/'reviews/gemini-3-flash-preview').glob('*.json'):
  if p.stem in hashes:
   r=json.loads(p.read_text())
   if r.get('status')=='success':reviews[p.stem]=r
 # One source/target training unit; translations never leak across grouped folds.
 units={}
 for p in pred:
  h=p.get('source_sha256');target=p.get('task',{}).get('target')
  if p.get('input_kind')!='raster'or target not in __import__('campaign.selector',fromlist=['TARGETS']).TARGETS or p['task'].get('operation')!='count'or p['task'].get('filters')or h not in reviews:continue
  units.setdefault((h,target),p)
 examples=[];unit_rows=[]
 for(h,target),p in units.items():
  g=gold[p['sample_id']];group=inv[g['path']]['group'];fold=int(hashlib.sha256(('selector-group-v1'+group).encode()).hexdigest()[:8],16)%5;candidates=proposals(p,reviews[h],words.get(h,{}).get('words',[]));indexes=[]
  for origin,candidate in candidates:
   x=features(p,candidate,origin,reviews[h],words.get(h,{}).get('words',[]),sizes[h]);assert len(x)==len(FEATURE_NAMES);indexes.append(len(examples));examples.append({'x':x,'y':int(candidate['answer']==g['answer']),'fold':fold,'group':group,'origin':origin,'answer':candidate['answer'],'sample_id':p['sample_id'],'target':target})
  unit_rows.append({'sample_id':p['sample_id'],'group':group,'fold':fold,'indices':indexes})
 atomic(folder/'training-manifest.json',{'time':now(),'parameters':PARAMETERS,'feature_names':FEATURE_NAMES,'examples':len(examples),'units':len(unit_rows),'drawings':len({r['group']for r in examples}),'review_sources':len(reviews),'split':'Canonical drawing/project inventory groups; sha256 selector-group-v1 modulo5; translations kept together','forbidden_features':['path','filename','question_id','reference_answer','correctness','drawing_id'],'numeric_rules_unchanged':True,'weights_policy':'Only model observations/proposed outputs and image/OCR properties are inference features'})
 X=np.asarray([r['x']for r in examples]);y=np.asarray([r['y']for r in examples]);models={}
 for fold in range(5):
  admit('optimize',90);ids=[i for i,r in enumerate(examples)if r['fold']!=fold];t=time.monotonic();model=train(X[ids],y[ids]);models[fold]=model;atomic(folder/('fold-'+str(fold)+'.json'),model);print('trained_fold',fold,'seconds',time.monotonic()-t,flush=True)
 oof=[]
 for p in pred:
  h=p.get('source_sha256');target=p.get('task',{}).get('target');g=gold[p['sample_id']]
  if(h,target)in units and not p['task'].get('filters')and p['task']['operation']=='count':
   group=inv[g['path']]['group'];fold=int(hashlib.sha256(('selector-group-v1'+group).encode()).hexdigest()[:8],16)%5;r=select(p,reviews[h],words.get(h,{}).get('words',[]),sizes[h],models[fold]);r['selector']['evaluation_fold']=fold
  else:r=p
  oof.append(r)
 (folder/'oof.predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in oof))
 model=train(X,y);model['training']={'drawings':len({r['group']for r in examples}),'examples':len(examples),'development_only':True,'reference_contract_sha256':sha(OUT/'baseline/contract.json'),'feature_source_sha256':sha(ROOT/'campaign/selector.py')};atomic(folder/'model.json',model);atomic(folder/'complete.json',{'time':now(),'model_sha256':sha(folder/'model.json'),'oof_predictions_sha256':sha(folder/'oof.predictions.jsonl'),'review_sources':len(reviews)});print('complete',len(reviews),len(examples),flush=True)
if __name__=='__main__':main()
