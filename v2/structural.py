from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Pinned RT-DETR-L structural adapter; author defaults, canonical pixel boxes.
Ultralytics RTDETRPredictor stretches to square, and scales XYXY to source shape.
No original drawing or annotations are modified. Local cache covers all five classes.
"""
import json,time,os
os.environ['YOLO_OFFLINE']='true'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['DO_NOT_TRACK']='1'
from pathlib import Path
from qa.common import ROOT,sha,write_json,inference_lock
from .supervisor import fresh_host,Admission
WEIGHTS=MODEL_ROOT/'rtdetr/rtdetr_l_autoresearch_60ep.pt'
SHA256='7c86051cc9f620f119ad16ee5c30a7c4893871ec8684897eac02e996d3307506'
CLASSES=['wall','door','window','railing','linkage_point']
SETTINGS={'imgsz':1024,'conf':.25,'iou':.5,'max_det':300,'device':'cpu','batch':1,'preprocess':'Ultralytics RTDETRPredictor scaleFill=True square stretch; source-space XYXY','version':'rtdetr-default-v1'}
_model=None

def parse(file):
 global _model
 import hashlib
 from demo_gpu import enabled,call,_last
 if enabled():
  gpu_cache=CACHE_ROOT/'v2-rtdetr'/(sha(file)+'-host-cuda-v1.json')
  if gpu_cache.exists():
   r=json.loads(gpu_cache.read_text());r['cache_hit']=True;_last.append(dict(r['execution'],cache_hit=True));return r
  try:
   with inference_lock():r=call(file,'rtdetr',{})
   write_json(gpu_cache,r);_last.append(r['execution']);return r
  except Exception as e:_last.append({'model':'RT-DETR-L','device':'cpu','fallback_reason':str(e)[:160]})
 key=sha(file)+'-'+hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'v2-rtdetr'/(key+'.json');t=time.perf_counter()
 if cache.exists():r=json.loads(cache.read_text());r['retrieval_seconds']=time.perf_counter()-t;r['cache_hit']=True;return r
 s=fresh_host()
 if Admission().check(s)!='admit':raise RuntimeError('Resource admission paused')
 with inference_lock():
  import torch
  torch.set_num_threads(2)
  from ultralytics import RTDETR
  cold=_model is None;load=time.perf_counter()
  if _model is None:
   if not WEIGHTS.exists():raise FileNotFoundError('RT-DETR weights not installed')
   if sha(WEIGHTS)!=SHA256:raise RuntimeError('RT-DETR checkpoint checksum mismatch')
   _model=RTDETR(str(WEIGHTS));assert [str(_model.names[i]) for i in range(5)]==CLASSES,repr(_model.names)
  loading=time.perf_counter()-load;infer=time.perf_counter()
  result=_model.predict(str(file),conf=.25,iou=.5,imgsz=1024,max_det=300,verbose=False,device='cpu',save=False)[0]
  entities=[]
  for i,(box,cls,score) in enumerate(zip(result.boxes.xyxy.tolist(),result.boxes.cls.tolist(),result.boxes.conf.tolist())):
   entities.append({'id':f'rtdetr-{i+1}','class':CLASSES[int(cls)],'bbox':box,'score':score,'source_sha256':sha(file),'provenance':'RT-DETR-L detector score, not calibrated probability'})
  r={'kind':'raster','entities':entities,'image_size':list(reversed(result.orig_shape)),'source_sha256':sha(file),'class_map':dict(enumerate(CLASSES)),'settings':SETTINGS,'model':{'name':'RT-DETR-L floorplan','source_revision':(WEIGHTS.parent/'revision.txt').read_text().strip(),'weight_sha256':SHA256,'training':'official CubiCasa5K4200 train per author; local membership unknown','license':'Ultralytics AGPL-3.0; dataset CC BY-NC-SA4.0; standalone checkpoint licence not explicitly supplied by author, no commercial rights claim'},'timing':{'model_loading_seconds':loading,'inference_seconds':time.perf_counter()-infer,'total_seconds':time.perf_counter()-t,'cold_model':cold},'peak_gpu_memory_bytes':None,'cache_hit':False}
  write_json(cache,r);return r

def answer(file,task):
 if task.get('operation')!='count' or task.get('target') not in ('window','door') or task.get('filters') or task.get('scope')=='model':
  raise ValueError('RT-DETR scoped count not supported')
 r=parse(file);entities=[e for e in r['entities'] if e['class']==task['target']]
 return {'device':r.get('execution',{}).get('device','cpu'),'peak_gpu_memory_bytes':r.get('peak_gpu_memory_bytes'),'status':'success','answer':len(entities),'unit':'count','evidence':entities,'route':'raster.rtdetr-l','model':r['model'],'structural_settings':r.get('settings',SETTINGS),'structural_timing':dict(r['timing'],cache_hit=r['cache_hit'],retrieval_seconds=r.get('retrieval_seconds')),'warnings':['Structural detector score is not calibrated probability; check omissions and class confusion. Zero is not verified absence.','Training overlap with these development plans is possible.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in entities]}]}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--output',required=True);a=p.parse_args();r=parse(a.image);write_json(a.output,r);print(json.dumps({'counts':{c:sum(e['class']==c for e in r['entities']) for c in CLASSES},'timing':r['timing'],'settings':r['settings']}))
