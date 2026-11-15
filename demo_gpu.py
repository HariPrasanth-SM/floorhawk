from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Optional authenticated host vision bridge; same weights/settings, explicit fallback."""
import os,json,base64,time
from pathlib import Path
from qa.common import ROOT
_enabled=False
_last=[]
def enabled():return os.environ.get('PROOFPLAN_HOST_VISION','0')=='1' and os.environ.get('PROOFPLAN_IN_HOST')!='1'
def call(file,model,settings):
 from v2.worker_client import request
 health=request(timeout=2)
 if not health.get('vision',False):raise RuntimeError('Host worker needs restart for vision support')
 body={'mode':'vision','model':model,'image_base64':base64.b64encode(Path(file).read_bytes()).decode(),'settings':settings}
 return request(body,timeout=180)
def install():
 global _enabled
 if _enabled:return
 _enabled=True
 os.environ.setdefault('PROOFPLAN_HOST_VISION','1')
 from qa.raster import CubiParser
 original=CubiParser.parse
 def parse(self,path):
  if enabled():
   try:
    r=call(path,'cubicasa',{'max_edge':self.max_edge,'rotations':self.rotations,'threads':self.threads,'ocr':self.ocr})
    if r.get('status')=='failed':raise RuntimeError(r.get('error','Host inference failed'))
    import numpy as np
    r['_maps']=[np.asarray(x,dtype=np.uint8)for x in r['_maps']];_last.append(r['execution']);return r
   except Exception as e:
    r=original(self,path);r['execution']={'device':'cpu','model':'CubiCasa5K','fallback_reason':str(e)[:160]};_last.append(r['execution']);return r
  return original(self,path)
 CubiParser.parse=parse

def _host_vision_impl(body):
 import tempfile,io,torch,numpy as np
 from PIL import Image
 from qa.common import sha
 from v2.supervisor import sample
 model=body.get('model');settings=body.get('settings',{})
 if model not in ('cubicasa','rtdetr','custom_yolo'):raise ValueError('Unknown configured vision model')
 raw=base64.b64decode(body['image_base64'],validate=True)
 if len(raw)>20*1024**2:raise ValueError('Image exceeds bound')
 im=Image.open(io.BytesIO(raw));im.load()
 if im.width*im.height>30_000_000:raise ValueError('Image dimensions exceed bound')
 # This authenticated internal operation is called while the app owns inference.lock.
 before=sample(gpu=True);torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
 if _host_models.get('kind')!=model:
  if _host_models.get('kind')=='custom_yolo':
   from custom_detector import release
   release()
  _host_models.clear();__import__('gc').collect();torch.cuda.empty_cache()
 with tempfile.NamedTemporaryFile(suffix='.png',dir=CACHE_ROOT)as f:
  f.write(raw);f.flush()
  if model=='custom_yolo':
   from custom_detector import infer
   _host_models.update(kind=model);r=infer(f.name,device='cuda:0',acquire_lock=False)
  elif model=='cubicasa':
   from qa.raster import CubiParser
   edge=settings.get('max_edge',512);rot=settings.get('rotations',[[0,0]])
   if edge not in (512,1024)or len(rot)>4 or any(list(x)not in [[0,0],[1,-1],[2,2],[-1,1]]for x in rot):raise ValueError('Unregistered parser settings')
   key=(edge,str(rot),bool(settings.get('ocr',False)))
   if _host_models.get('key')!=key:_host_models.clear();_host_models.update(kind=model,key=key,parser=CubiParser('0',edge,rotations=rot,threads=2,ocr=bool(settings.get('ocr',False))))
   r=_host_models['parser'].parse(f.name);r['_maps']=[x.tolist()for x in r['_maps']]
  else:
   from v2.structural import WEIGHTS,SHA256,CLASSES,SETTINGS
   from ultralytics import RTDETR
   if sha(WEIGHTS)!=SHA256:raise ValueError('Checkpoint hash mismatch')
   if 'net'not in _host_models:_host_models.update(kind=model,net=RTDETR(str(WEIGHTS)))
   net=_host_models['net'];t=time.perf_counter();prediction=net.predict(f.name,conf=.25,iou=.5,imgsz=1024,max_det=300,device=0,verbose=False,save=False)[0];torch.cuda.synchronize()
   r={'kind':'raster','image_size':list(reversed(prediction.orig_shape)),'source_sha256':sha(f.name),'entities':[{'id':f'rtdetr-{i+1}','class':CLASSES[int(c)],'bbox':b,'score':s,'source_sha256':sha(f.name),'provenance':'RT-DETR detector score, not probability'}for i,(b,c,s)in enumerate(zip(prediction.boxes.xyxy.tolist(),prediction.boxes.cls.tolist(),prediction.boxes.conf.tolist()))],'model':{'name':'RT-DETR-L floorplan','weight_sha256':SHA256},'settings':dict(SETTINGS,device='cuda:0'),'class_map':dict(enumerate(CLASSES)),'timing':{'inference_seconds':time.perf_counter()-t,'total_seconds':time.perf_counter()-started,'cold_model':False},'cache_hit':False}
  device=r['execution']['device']if model=='custom_yolo'else str(next((_host_models['parser'].model if model=='cubicasa'else _host_models['net'].model).parameters()).device)
  # Cubi reference releases to CPU after actual CUDA tensor execution, recorded separately.
  r['execution']={'device':'cuda:0','parameter_device_after':device,'executing_pid':os.getpid(),'model':model,'peak_gpu_memory_bytes':torch.cuda.max_memory_allocated(),'gpu_before':before,'gpu_after':sample(gpu=True),'runtime_seconds':time.perf_counter()-started,'cache_hit':False};r['peak_gpu_memory_bytes']=r['execution']['peak_gpu_memory_bytes'];return r
_host_models={}


def host_vision(body):
 import torch
 devices=set()
 def capture(module,args):
  for arg in args:
   if isinstance(arg,torch.Tensor):devices.add(str(arg.device))
 hook=torch.nn.modules.module.register_module_forward_pre_hook(capture)
 try:
  torch.cuda.set_per_process_memory_fraction(.60)
  result=_host_vision_impl(body)
  if 'cuda:0'not in devices:raise RuntimeError('No CUDA model input tensor observed')
  result['execution']['observed_tensor_devices']=sorted(devices)
  return result
 finally:hook.remove()

def release_host_models():
 if _host_models.get('kind')=='custom_yolo':
  from custom_detector import release
  release()
 _host_models.clear()
 import gc,torch
 gc.collect()
 if torch.cuda.is_available():torch.cuda.empty_cache()
