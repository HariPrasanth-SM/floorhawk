"""Resident installed models, fresh answers, inspectable specialist/Gemini routing."""
import os,time,json,uuid,shutil,base64,copy,hashlib
from pathlib import Path

def route_reason(local):
 if local.get('status')!='success' or local.get('answer')is None:return None
 route=local.get('route','');task=local.get('task',{});e=local.get('evidence',[])
 if route.startswith('ifc.'):return 'Explicit IFC entity/property query; declared scope/units checked by existing tools'
 if route.startswith('pdf.')and'raster'not in route and(e or local.get('answer')==0):return 'Native PDF text/vector/label evidence with existing scope and unit checks'
 if route=='raster.rtdetr-l.v3'and task.get('target')in ['door','window']and local.get('coverage',{}).get('complete')is not False:
  ids=[r.get('id')for r in e];count=local.get('answer')
  if isinstance(count,int)and count>0 and len(ids)==len(set(ids))==count:return 'Existing specialist detection and duplicate suppression; unique source instances support the count'
 return None

class Runtime:
 def __init__(self,publish=None):
  import torch
  import demo_gpu
  from runtime_paths import CACHE_ROOT,MODEL_ROOT
  self.cache=CACHE_ROOT;self.cache.mkdir(parents=True,exist_ok=True);self.worker_id=uuid.uuid4().hex;self.loads={'cubicasa':0,'rtdetr':0,'ocr':0};t=time.perf_counter();self.boot=time.time();torch.set_num_threads(2);torch.cuda.set_per_process_memory_fraction(.60)
  import sys
  sys.path.insert(0,str(MODEL_ROOT/'cubicasa-compatible'))
  from floortrans.models.hg_furukawa_original import hg_furukawa_original
  from qa.common import sha
  from qa.raster import CubiParser,WEIGHT_SHA
  from v2.supervisor import Admission
  self.resource_admission=Admission()
  if sha(MODEL_ROOT/'cubicasa-model.pkl')!=WEIGHT_SHA:raise ValueError('CubiCasa hash mismatch')
  self.cubi=hg_furukawa_original(44);self.cubi.load_state_dict(torch.load(MODEL_ROOT/'cubicasa-model.pkl',map_location='cpu',weights_only=False)['model_state'],strict=True);self.cubi.eval().to('cuda:0');self.loads['cubicasa']=1
  from ultralytics import RTDETR
  from v2.structural import WEIGHTS,SHA256,CLASSES
  if sha(WEIGHTS)!=SHA256:raise ValueError('RT-DETR hash mismatch')
  self.rt=RTDETR(str(WEIGHTS));self.rt.model.to('cuda:0');self.loads['rtdetr']=1
  original=CubiParser.parse;runtime=self
  def parse(parser,path):
   before=runtime.gpu_admission()
   parser.model=runtime.cubi;parser.device='0';parser.keep_gpu=True;devices=set()
   hook=torch.nn.modules.module.register_module_forward_pre_hook(lambda m,args:devices.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
   try:r=original(parser,path)
   finally:hook.remove()
   if 'cuda:0'not in devices:raise RuntimeError('CUDA tensor not observed')
   ex={'model':'CubiCasa5K','device':'cuda:0','observed_tensor_devices':sorted(devices),'worker_id':runtime.worker_id,'load_counts':dict(runtime.loads),'cache_hit':False,'peak_gpu_memory_bytes':r.get('peak_gpu_memory_bytes'),'gpu_before':before,'gpu_after':runtime.resource_sample()};r['execution']=ex;demo_gpu._last.append(ex);return r
  CubiParser.parse=parse;demo_gpu._enabled=True;demo_gpu.enabled=lambda:True
  def detect(file,model,settings):
   if model!='rtdetr':raise ValueError('Only registered RT-DETR RPC role is used')
   before=runtime.gpu_admission()
   started=time.perf_counter();devices=set();hook=torch.nn.modules.module.register_module_forward_pre_hook(lambda m,args:devices.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
   try:p=runtime.rt.predict(str(file),conf=.25,iou=.5,imgsz=1024,max_det=300,device=0,verbose=False,save=False)[0];torch.cuda.synchronize()
   finally:hook.remove()
   if 'cuda:0'not in devices:raise RuntimeError('CUDA tensor not observed')
   from v2.structural import SETTINGS
   ex={'model':'RT-DETR-L','device':'cuda:0','observed_tensor_devices':sorted(devices),'worker_id':runtime.worker_id,'load_counts':dict(runtime.loads),'cache_hit':False,'peak_gpu_memory_bytes':torch.cuda.max_memory_allocated(),'gpu_before':before,'gpu_after':runtime.resource_sample()}
   return {'kind':'raster','source_sha256':sha(file),'image_size':list(reversed(p.orig_shape)),'entities':[{'id':'rtdetr-'+str(i+1),'class':CLASSES[int(c)],'bbox':b,'score':s,'provenance':'RT-DETR-L detector score, not probability'}for i,(b,c,s)in enumerate(zip(p.boxes.xyxy.tolist(),p.boxes.cls.tolist(),p.boxes.conf.tolist()))],'model':{'name':'RT-DETR-L','weight_sha256':SHA256},'settings':SETTINGS,'class_map':dict(enumerate(CLASSES)),'execution':ex,'timing':{'inference_seconds':time.perf_counter()-started,'model_loading_seconds':0},'cache_hit':False}
  demo_gpu.call=detect
  import v2.supervisor
  v2.supervisor.fresh_host=lambda:v2.supervisor.sample(gpu=True)
  try:
   import v2.ocr
   v2.ocr.engine();self.loads['ocr']=1
  except Exception as exc:self.ocr_warning=type(exc).__name__
  import qa_app,v2.budget,v2.gemini
  from deploy.modal.presenter_budget import PresenterLedger
  v2.budget.Ledger=PresenterLedger;v2.gemini.Ledger=PresenterLedger
  self.publish=publish
  original_write=qa_app.write_json
  def publish_write(path,data):
   if Path(path).name=='job.json'and data.get('status')in['success','failed']:
    self.pending_terminal=copy.deepcopy(data);return
   original_write(path,data)
   local=data.get('local_prediction')if Path(path).name=='job.json'else None
   if publish and Path(path).name=='job.json'and not(local and route_reason(local)):publish()
  qa_app.write_json=publish_write
  self.app=qa_app.Application('cpu');self.app.samples=[];self.app.pipeline.set_cloud(True);self.app.pipeline.local_routing=False;self.app.paired.provider=v2.gemini.generate
  original_local=self.app.paired.local
  def local_answer(file,question,sample_id=None,progress=None):
   from qa.router import route
   task=route(question)
   if Path(file).suffix.lower()in ['.png','.jpg','.jpeg']and task.get('operation')=='count'and task.get('target')in ['door','window']and not task.get('filters')and task.get('scope')!='model':
    from v2.structural_tuned import answer
    from v2.structural import parse as raw_parse
    from qa.common import write_json
    started=time.perf_counter();result=answer(file,task);facts=raw_parse(file);folder=self.app.paired.output/'direct-specialist';folder.mkdir(exist_ok=True);bundle=folder/'evidence.json'
    if not bundle.exists():write_json(bundle,{'facts':facts,'source_sha256':sha(file),'configuration':self.app.paired.config,'shared_processing':{'cache_hit':False,'note':'Fresh direct specialist forward; no unrelated segmentation run'}})
    projection=folder/('query-'+hashlib.sha256(json.dumps([question,task],sort_keys=True).encode()).hexdigest()+'.json');write_json(projection,{'evidence':result.get('evidence',[]),'task':task,'question':question})
    result.update(request_id=uuid.uuid4().hex,task=task,input_kind='raster',question=question,source_sha256=sha(file),device='cuda:0',timing={'total_seconds':time.perf_counter()-started,'cache_hit':False,'inference_seconds':facts.get('timing',{}).get('inference_seconds')},stage_timings={},shared_evidence={'path':str(bundle),'sha256':sha(bundle),'key':folder.name},question_evidence={'path':str(projection),'sha256':sha(projection)},paired_timing={'shared_preprocessing_seconds_charged':time.perf_counter()-started,'local_answer_seconds':0,'note':'Direct registered door/window specialist; source/target/scope rule, no identity or reference lookup'})
    return result
   return original_local(file,question,sample_id,progress)
  self.app.paired.local=local_answer
  original_hybrid=self.app.paired.hybrid
  def final(file,question,local):
   reason=route_reason(local)
   if reason:return {'status':'success','answer':local['answer'],'unit':local.get('unit'),'evidence_ids':[r.get('id',r.get('guid'))for r in local.get('evidence',[])],'explanation':reason,'provider_invoked':False,'provider_attempts':0,'supporting_tool':local.get('route'),'chosen_route':'deterministic-specialist','route_reason':reason,'generation':[],'timing':{'additional_gemini_seconds':0}}
   result=original_hybrid(file,question,local);result.update(chosen_route='gemini-evidence-review',route_reason='Local result not covered by a trusted general specialist rule')
   task=local.get('task',{});target=task.get('target');aliases={'shower_bath':{'shower','bathtub'}}.get(target,{target})
   if result.get('status')=='success'and local.get('status')=='success'and result.get('answer')!=local.get('answer')and task.get('operation')=='count'and target in ['window','door','sink','toilet_fixture','shower_bath']:
    facts=json.loads(Path(local['shared_evidence']['path']).read_text()).get('facts',{});lookup={e.get('id'):e for e in facts.get('entities',[])+local.get('evidence',[])}
    supported={i for i in result.get('evidence_ids',[])if i in lookup and lookup[i].get('class')in aliases and lookup[i].get('bbox')}
    local_supported={e.get('id')for e in local.get('evidence',[])if e.get('class')in aliases and e.get('bbox')}
    if len(supported)!=result.get('answer'):
     result['original_gemini_review']=copy.deepcopy(result)
     if len(local_supported)==local.get('answer')and local.get('answer',0)>0:
      result.update(answer=local['answer'],unit=local.get('unit'),evidence_ids=list(local_supported),chosen_route='specialist-retained',route_reason='Numerical Gemini correction lacks matching unique target-instance evidence; retained supported specialist instances',explanation='Retained the local specialist count supported by its source instances; the review did not localize its proposed correction.')
     else:result.update(status='abstained',answer=None,chosen_route='insufficient-count-evidence',route_reason='Disputed numerical count lacks supporting instance evidence',explanation='The conflicting counts cannot be established from the recorded instances.')
   return result
  self.app.paired.hybrid=final
  # Warm kernels on blank inputs, never on curated questions/answers.
  import numpy as np
  with torch.inference_mode():self.cubi(torch.zeros((1,3,128,128),device='cuda:0'));self.rt.predict(np.zeros((256,256,3),dtype=np.uint8),imgsz=1024,device=0,verbose=False)
  torch.cuda.synchronize();self.initialization_seconds=time.perf_counter()-t;self.calls=0
 def resource_sample(self):
  from v2.supervisor import sample
  return sample(os.getpid(),gpu=True)
 def gpu_admission(self):
  current=self.resource_sample();decision=self.resource_admission.check(current,require_gpu=True)
  if decision!='admit':raise RuntimeError('GPU resource admission '+decision+'; no forward launched')
  return current
 def readiness(self):
  import torch,psutil
  return {'ready':True,'worker_id':self.worker_id,'pid':os.getpid(),'loads':self.loads,'calls':self.calls,'initialization_seconds':self.initialization_seconds,'additional_startup':getattr(self,'extra_startup',None),'gpu':'T4','allocated_gpu_bytes':torch.cuda.memory_allocated(),'reserved_gpu_bytes':torch.cuda.memory_reserved(),'peak_allocated_gpu_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_gpu_bytes':torch.cuda.max_memory_reserved(),'rss_bytes':psutil.Process().memory_info().rss,'ocr_warning':getattr(self,'ocr_warning',None),'warm_inputs':'blank tensors only; no gallery predictions cached'}
 def run(self,ident):
  from qa.common import write_json
  import qa_app
  import torch
  torch.cuda.reset_peak_memory_stats();started=time.time();self.calls+=1;self.pending_terminal=None
  # Only task-owned scratch caches are cleared; models/engines remain resident.
  shutil.rmtree(self.cache);self.cache.mkdir();(self.cache/'qa').mkdir();self.app.pipeline.base.memory.clear();self.app.paired.documents.clear()
  key=os.environ.get('GEMINI_API_KEY')or os.environ.get('GOOGLE_API_KEY')or os.environ.get('API_KEY')
  if key:p=self.cache/'gemini.key';p.write_text(key);p.chmod(0o600);os.environ['PROOFPLAN_GEMINI_KEY_FILE']=str(p)
  job=json.loads((qa_app.STORE/ident/'job.json').read_text());job['_submitted_perf']=time.perf_counter();self.app.jobs[ident]=job;self.app.paired.output=qa_app.STORE/ident/'evidence-bundles';self.app.paired.output.mkdir(exist_ok=True)
  self.app.execute(ident);path=qa_app.STORE/ident/'job.json';job=self.pending_terminal or copy.deepcopy(self.app.jobs[ident]);h=job.get('prediction',{}).get('paired',{}).get('hybrid',{});job['resident']=self.readiness();job['resident']['call_index']=self.calls;job['release']=json.loads(Path('/opt/floorhawk/release.json').read_text());job['presenter_timing']={'queue_and_api_seconds':max(0,started-job['created']),'worker_seconds':time.time()-started,'end_to_end_seconds':time.time()-job['created'],'model_initialization_seconds':self.initialization_seconds if self.calls==1 else 0,'gemini_seconds':h.get('timing',{}).get('additional_gemini_seconds'),'local':job.get('prediction',{}).get('paired_timing',{}),'note':'Queue/API delay combined; model initialization separately recorded at resident startup'};write_json(path,job);return job['status']
