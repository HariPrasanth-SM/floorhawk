from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Count-supervised inclusion calibration; real boxes only, no fallback counts.
This score has not been spatially calibrated and is not a probability of correctness.
"""
import json,math,hashlib
from qa.common import ROOT,sha
from .dedup import suppress
MODEL=MODEL_ROOT/'v3-weak-box/calibration.json'
FEATURE_VERSION='box-geometry-logit-v1'
def features(e,size):
 w,h=size;b=e['bbox'];bw=max(1e-6,b[2]-b[0]);bh=max(1e-6,b[3]-b[1]);s=max(.001,min(.999,e['score']));mn=min(bw/w,bh/h);mx=max(bw/w,bh/h)
 return [1.,math.log(s/(1-s)),math.log(max(1e-6,bw*bh/(w*h))),abs(math.log(bw/bh)),mn,mx,(b[0]+b[2])/(2*w),(b[1]+b[3])/(2*h),float(min(b[0]/w,b[1]/h,(w-b[2])/w,(h-b[3])/h)<.025)]
def apply(raw,model=None):
 model=model or json.loads(MODEL.read_text())
 if model['feature_version']!=FEATURE_VERSION:raise ValueError('Weak calibration feature version mismatch')
 selected={};removed={};entities,_=suppress(raw['entities'],'fragments85')
 for cls in ('door','window'):
  c=model['classes'][cls];kept=[];dropped=[]
  for e in entities:
   if e['class']!=cls:continue
   f=features(e,raw['image_size']);z=sum(a*b for a,b in zip(f,c['coefficients']));score=1/(1+math.exp(-max(-40,min(40,z))));e=dict(e,weak_inclusion_score=score)
   (kept if score>=c['threshold'] else dropped).append(e)
  selected[cls]=kept;removed[cls]=dropped
 return selected,removed
