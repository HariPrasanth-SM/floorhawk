"""General source-format/task specialist selection, independent of grading and IDs."""
import copy,hashlib,json
from pathlib import Path
VERSION='overnight-specialist-router-v1'
TARGET_CLASSES={'door':['door'],'window':['window'],'sink':['sink'],'toilet_fixture':['toilet_fixture'],'shower_bath':['shower','bathtub'],'shower':['shower'],'bathtub':['bathtub'],'stair':['stair']}
def suppress(entities,threshold,iou=.5):
 from v3.dedup import overlap
 selected=[]
 for e in sorted(entities,key=lambda r:r.get('score',0),reverse=True):
  if e.get('score',0)<threshold:continue
  if any(e['class']==k['class']and overlap(e['bbox'],k['bbox'])[0]>iou for k in selected):continue
  selected.append(copy.deepcopy(e))
 return selected
def apply(local,observation,config):
 task=local.get('task',{});target=task.get('target');policy=config.get('targets',{}).get(target)
 if not policy or task.get('operation')!='count' or task.get('filters')or task.get('scope')=='model'or local.get('input_kind')!='raster':return copy.deepcopy(local)
 if observation.get('status')!='success'or observation.get('coverage',{}).get('complete')is False:return copy.deepcopy(local)
 if observation['source_sha256']!=local['source_sha256']:raise ValueError('Incompatible observation source')
 if observation['model']['weight_sha256']!=config['custom_weight_sha256']:raise ValueError('Incompatible observation weight')
 classes=TARGET_CLASSES.get(target)
 if not classes:return copy.deepcopy(local)
 entities=[e for e in observation.get('entities',[])if e['class']in classes];selected=suppress(entities,policy['confidence'],policy['iou']);r=copy.deepcopy(local)
 r['previous_local']={k:copy.deepcopy(local.get(k))for k in ['status','answer','unit','route','evidence']};r.update(status='success',answer=len(selected),unit='count',evidence=selected,route='raster.custom-yolo.campaign-v1',model=observation['model'],candidate_policy={'version':VERSION,'target':target,'settings':policy,'reason':'Development-validated existing specialist for this task class; numerical count equals included unique detections','observation_key':observation.get('cache_key')},calculation_trace=[{'operation':'count_unique_included_entities','ids':[e['id']for e in selected],'value':len(selected)}]);r['warnings']=list(r.get('warnings',[]))+['Existing custom detector selected using development evidence; pretrained/custom training overlap unknown. Zero does not establish absence.'];return r
