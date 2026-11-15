"""Additional already installed CubiCasa/inclusion-head proposals, no references."""
import copy
from v3.dedup import overlap

def extend(local,rt,cubi512,cubi1024):
 target=local['task']['target'];out=[]
 for name,facts in [('cubi512',cubi512),('cubi1024',cubi1024)]:
  if not facts:continue
  entities=[e for e in facts.get('entities',[])if e.get('kind')=='icon'and e['class']==target];kept=[]
  for e in sorted(entities,key=lambda e:(e['bbox'][2]-e['bbox'][0])*(e['bbox'][3]-e['bbox'][1]),reverse=True):
   if not any(overlap(e['bbox'],k['bbox'])[0]>.5 or overlap(e['bbox'],k['bbox'])[1]>.85 for k in kept):kept.append(e)
  for profile,rows in [('raw',entities),('dedup',kept)]:
   r=copy.deepcopy(local);r.update(answer=len(rows),evidence=copy.deepcopy(rows),status='success',unit='count',route='raster.native-cubicasa-opening-proposal.campaign-v1',opening_profile={'source':name,'profile':profile});out.append((name+':'+profile,r))
 if rt and cubi512 and rt.get('image_size')==cubi512.get('image_size'):
  from v3.cross_boxes import apply
  e,_=apply(rt,cubi512);r=copy.deepcopy(local);r.update(answer=len(e[target]),evidence=e[target],status='success',route='raster.existing-cross-inclusion-proposal.campaign-v1');out.append(('cross-head',r))
 if rt:
  from v3.weak_boxes import apply
  e,_=apply(rt);r=copy.deepcopy(local);r.update(answer=len(e[target]),evidence=e[target],status='success',route='raster.existing-weak-inclusion-proposal.campaign-v1');out.append(('weak-head',r))
 return out
