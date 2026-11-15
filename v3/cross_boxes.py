from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Weak inclusion calibration combining real RT boxes and CubiCasa icon geometry.
No reference counts at runtime; original RT boxes/scores and support sources retained.
"""
import json,math
from qa.common import ROOT
from .dedup import suppress,overlap
from .weak_boxes import features as base_features
MODEL=MODEL_ROOT/'v3-cross-box/calibration.json'
FEATURE_VERSION='rtdetr-cubicasa-geometry-support-v1'
def features(e,size,cubi):
 b=e['bbox'];same=[o for o in cubi['entities'] if o.get('kind')=='icon' and o['class']==e['class']];other=[o for o in cubi['entities'] if o.get('kind')=='icon' and o['class']==('door' if e['class']=='window' else 'window')];closets=[o for o in cubi['entities'] if o.get('kind')=='icon' and o['class']=='closet'];appliances=[o for o in cubi['entities'] if o.get('kind')=='icon' and o['class']=='electrical_appliance'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;diag=math.hypot(*size)
 def maximum(items,k=0):return max((overlap(b,o['bbox'])[k] for o in items),default=0.)
 distance=min((math.hypot(cx-(o['bbox'][0]+o['bbox'][2])/2,cy-(o['bbox'][1]+o['bbox'][3])/2)/diag for o in same),default=1.)
 inside=any(o['bbox'][0]<=cx<=o['bbox'][2] and o['bbox'][1]<=cy<=o['bbox'][3] for o in same)
 return base_features(e,size)+[maximum(same),maximum(same,1),maximum(other),maximum(closets),distance,float(bool(same)),maximum(appliances),float(inside)]
def apply(raw,cubi,model=None):
 if raw['source_sha256']!=cubi['source_sha256'] or raw['image_size']!=cubi['image_size']:raise ValueError('Cross-model source/frame mismatch')
 model=model or json.loads(MODEL.read_text())
 if model['feature_version']!=FEATURE_VERSION:raise ValueError('Cross-box feature version mismatch')
 entities,_=suppress(raw['entities'],'fragments85');selected={};removed={}
 for cls in ('window','door'):
  config=model['classes'][cls];kept=[];dropped=[]
  if len(config['coefficients'])!=17:raise ValueError('Cross-box coefficient shape mismatch')
  for e in entities:
   if e['class']!=cls:continue
   f=features(e,raw['image_size'],cubi);z=sum(a*b for a,b in zip(f,config['coefficients']));score=1/(1+math.exp(-max(-40,min(40,z))));item=dict(e,weak_inclusion_score=score,cross_model_support_features=f)
   (kept if score>=config['threshold'] else dropped).append(item)
  selected[cls]=kept;removed[cls]=dropped
 return selected,removed
