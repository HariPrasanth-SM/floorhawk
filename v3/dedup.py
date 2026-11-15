"""Class-aware deterministic duplicate/fragment suppression on real detections.
Raw predictions stay immutable. No reference counts, filenames or labels are inputs.
"""
import copy
PROFILES={'raw':{},'nms50':{'iou':.5},'fragments85':{'iou':.5,'containment':.85},'conf50_fragments85':{'iou':.5,'containment':.85,'confidence':.5}}
for threshold in (.35,.65,.8,.9):PROFILES['conf'+str(int(threshold*100))+'_fragments85']={'iou':.5,'containment':.85,'confidence':threshold}
def overlap(a,b):
 x=max(0,min(a[2],b[2])-max(a[0],b[0]));y=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=x*y;aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]);bb=max(0,b[2]-b[0])*max(0,b[3]-b[1]);return inter/max(aa+bb-inter,1e-9),inter/max(min(aa,bb),1e-9)
def suppress(entities,profile):
 config=PROFILES[profile];kept=[];removed=[]
 for e in sorted(copy.deepcopy(entities),key=lambda e:e.get('score',0),reverse=True):
  if e.get('score',0)<config.get('confidence',0):removed.append({'entity':e,'reason':'confidence'});continue
  duplicate=None
  for k in kept:
   if k['class']!=e['class']:continue
   iou,ios=overlap(k['bbox'],e['bbox'])
   if iou>config.get('iou',1.01) or ios>config.get('containment',1.01):duplicate=k;break
  if duplicate:removed.append({'entity':e,'reason':'overlap duplicate/fragment hypothesis','kept_id':duplicate['id']})
  else:kept.append(e)
 return kept,removed
