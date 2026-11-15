"""Provider-free CPU fallback for the frozen Local evaluation contract.

Uses existing adapters and candidate pure postprocessing. CPU/CUDA numerical
differences and this explicit backend are retained, never called Hybrid scoring.
"""
import time,json,hashlib,base64,copy
from pathlib import Path
from campaign.clock import DEADLINES
from campaign.final_contract import validate_questions
from qa.common import sha,write_json,inference_lock
from runtime_paths import CACHE_ROOT,RESULTS_ROOT

class CPUFinal:
 def __init__(self,release):
  import torch,demo_gpu,v2.supervisor,v2.gemini
  from v3.pipeline import Pipeline
  torch.set_num_threads(2);demo_gpu.enabled=lambda:False;v2.supervisor.fresh_host=lambda:v2.supervisor.sample(gpu=False)
  def blocked(*args,**kwargs):raise RuntimeError('Provider forbidden in frozen Local CPU evaluation')
  v2.gemini.generate=blocked;self.pipeline=Pipeline('cpu');self.pipeline.set_cloud(False);self.pipeline.local_routing=False
  from qa.raster import CubiParser
  self.pipeline.base.raster=CubiParser('cpu',self.pipeline.max_edge,threads=2)
  self.release=release;self.config=json.loads((Path(__file__).resolve().parents[1]/'config/overnight-candidate.json').read_text());self.custom=None;self.loads=0
 def observe(self,file):
  from custom_detector import weights_path,WEIGHT_SHA256,RAW_CLASSES
  from campaign.live_adapter import detector_entities
  import torch
  h=sha(file);settings={'imgsz':1024,'conf':.05,'iou':.7,'max_det':500,'device':'cpu','version':'overnight-yolo-observations-v1'};key=hashlib.sha256(json.dumps([h,WEIGHT_SHA256,settings,self.release],sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'campaign-custom'/(key+'.json')
  if cache.exists():r=json.loads(cache.read_text());r['execution']['cache_hit']=True;return r
  import v2.supervisor
  if v2.supervisor.Admission().check(v2.supervisor.sample(gpu=False))!='admit':raise RuntimeError('CPU resource pressure; no model forward')
  started=time.perf_counter()
  with inference_lock():
   if self.custom is None:
    from ultralytics import YOLO
    path=weights_path()
    if sha(path)!=WEIGHT_SHA256:raise ValueError('Frozen custom weight mismatch')
    self.custom=YOLO(str(path));self.custom.model.to('cpu');self.loads+=1
   if list(self.custom.names.values())!=RAW_CLASSES:raise ValueError('Frozen class-map mismatch')
   devices=set();hook=self.custom.model.register_forward_pre_hook(lambda model,args:devices.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
   try:prediction=self.custom.predict(str(file),device='cpu',imgsz=1024,conf=.05,iou=.7,max_det=500,verbose=False,save=False)[0]
   finally:hook.remove()
  if 'cpu'not in devices:raise RuntimeError('CPU input tensor not observed')
  r={'status':'success','source_sha256':h,'image_size':list(reversed(prediction.orig_shape)),'entities':detector_entities(prediction,h),'model':{'name':'Supplied YOLO11m','weight_sha256':WEIGHT_SHA256,'classes':RAW_CLASSES},'settings':settings,'cache_key':key,'execution':{'device':'cpu','observed_tensor_devices':sorted(devices),'cache_hit':False,'inference_seconds':time.perf_counter()-started,'loads':self.loads}};write_json(cache,r);return r
 def local(self,file,question,output):
  from qa.router import route
  from campaign.live_adapter import direct_fixture
  task=route(question);raster=file.suffix in ['.png','.jpg','.jpeg'];unfiltered=task.get('operation')=='count'and not task.get('filters')and task.get('scope')!='model';started=time.perf_counter()
  if raster and unfiltered and task.get('target')in self.config['targets']:
   obs=self.observe(file);return direct_fixture(file,question,task,obs,self.config,output,time.perf_counter()-started)
  if raster and unfiltered and task.get('target')in ['door','window']:
   from v2.structural_tuned import answer
   r=answer(file,task);r.update(task=task,input_kind='raster',source_sha256=sha(file),question=question,timing={'total_seconds':time.perf_counter()-started,'cache_hit':r.get('structural_timing',{}).get('cache_hit')})
   if task['target']in self.config.get('ensemble',{}):
    from v2.structural import parse
    from campaign.ensemble import instances
    rt=parse(file);custom=self.observe(file);e=instances(rt['entities'],custom['entities'],task['target'],self.config['ensemble'][task['target']]);r.update(answer=len(e),evidence=e,status='success',unit='count',route='raster.instance-corroboration.campaign-v1')
   return r
  r=self.pipeline.answer(file,question,sample_id=None,mode='local')
  if file.suffix=='.pdf'and r.get('status')!='success'and task.get('operation')in ['area','count']and task.get('target')in ['room','apartment']:
   from campaign.pdf_quantities import recover
   from qa.tools import pdf_answer
   proposal=pdf_answer(recover(file),task,question)
   if proposal['status']=='success':r.update(proposal,route='pdf.prefixed-native-room-evidence.campaign-v3')
  return r
 def evaluate(self,h,extension,encoded,questions,release,deadline):
  validate_questions(questions)
  if extension not in ['.png','.jpg','.jpeg','.pdf','.ifc']:raise ValueError('Unsupported evaluation source format')
  if release!=self.release or time.time()<DEADLINES['optimize']:raise RuntimeError('Frozen evaluation not admitted')
  raw=base64.b64decode(encoded,validate=True)
  if hashlib.sha256(raw).hexdigest()!=h or len(raw)>20*1024**2:raise ValueError('Source hash/byte bound')
  folder=RESULTS_ROOT/'overnight-20261115/final-local/source-work'/release/h;folder.mkdir(exist_ok=True,parents=True);file=folder/('source'+extension);file.write_bytes(raw);self.pipeline.base.memory.clear();started=time.perf_counter();rows=[]
  unsupported=None
  if extension in ['.png','.jpg','.jpeg']:
   from PIL import Image
   with Image.open(file)as im:
    if im.width*im.height>8_000_000:unsupported='Frozen evaluation8MP bound; no reduced-preview-only substitute'
  elif extension=='.pdf':
   import pymupdf
   with pymupdf.open(file)as doc:
    if len(doc)>20:unsupported='Frozen evaluation20page bound'
  elif len(raw)>10*1024**2 or raw.count(b'=IFC')>100000:unsupported='Frozen evaluationIFC complexity bound'
  for q in questions:
   if time.time()+8>deadline:break
   start=time.perf_counter()
   try:r={'status':'unsupported','answer':None,'unit':None,'evidence':[],'coverage':{'complete':False},'warnings':[unsupported]}if unsupported else self.local(file,q['question'],folder/'bundles')
   except Exception as exc:r={'status':'failed','answer':None,'unit':None,'evidence':[],'error':type(exc).__name__+': '+str(exc)[:240]}
   r.update(sample_id=q['sample_id'],question=q['question'],source_sha256=h,source_commit=release,execution_mode='frozen-local-cpu-evaluation',evaluation_query_seconds=time.perf_counter()-start);rows.append(r)
  return {'source_sha256':h,'source_commit':release,'rows':rows,'observations':[],'source_seconds':time.perf_counter()-started,'resident':{'device':'cpu','custom_loads':self.loads},'provider_attempts':0}
