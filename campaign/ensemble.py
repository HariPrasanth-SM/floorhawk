"""Instance-level detector corroboration; never average or look up numerical counts."""
import copy
from v3.dedup import overlap
from .candidate import suppress
PROFILES={'corroborated':{'fallback':True,'match_conf':.4,'add_conf':None},'strict':{'fallback':.8,'match_conf':.4,'add_conf':.8},'intersection':{'fallback':False,'match_conf':.4,'add_conf':None},'union70':{'fallback':True,'match_conf':1.1,'add_conf':.7},'union60_strong':{'fallback':.75,'match_conf':1.1,'add_conf':.6}}
def instances(rt,custom,target,profile):
 cfg=PROFILES[profile];a=[dict(e,id='rt:'+e['id'],origin_model='RT-DETR')for e in rt if e['class']==target];b=[dict(e,id='custom:'+e['id'],origin_model='Custom YOLO')for e in custom if e['class']==target];kept=[]
 def matches(x,y):
  iou,ios=overlap(x['bbox'],y['bbox']);return iou>=.2 or ios>=.65
 for e in a:
  support=[k['id']for k in b if k.get('score',0)>=cfg['match_conf']and matches(e,k)];threshold=(.65 if target=='door'else.5)if cfg['fallback']is True else cfg['fallback']if cfg['fallback']is not False else 1.1
  if support or e.get('score',0)>=threshold:e.update(corroborating_ids=support);kept.append(e)
 if cfg['add_conf']is not None:
  for e in b:
   if e.get('score',0)>=cfg['add_conf']and not any(matches(e,k)for k in kept):kept.append(e)
 # Same-class spatial duplicate/fragment suppression, preserving distinct nearby instances.
 final=[]
 for e in sorted(kept,key=lambda e:e.get('score',0),reverse=True):
  if not any(overlap(e['bbox'],k['bbox'])[0]>.5 or overlap(e['bbox'],k['bbox'])[1]>.85 for k in final):final.append(e)
 return final
