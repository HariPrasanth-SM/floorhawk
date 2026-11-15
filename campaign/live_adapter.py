"""Optional verified campaign specialists/selector on the existing resident pipeline.
No evaluator, drawing manifest, question IDs or reference resources are imported.
"""
import os,json,time,hashlib,copy
from pathlib import Path
from qa.common import sha,write_json
from runtime_paths import MODEL_ROOT,CACHE_ROOT
from .candidate import apply,TARGET_CLASSES
from .ensemble import instances

def review_failure(exc,stage):
 from v2.budget import BudgetBlocked
 from v2.gemini import ProviderBlocked
 status='blocked'if isinstance(exc,(BudgetBlocked,ProviderBlocked))else'validation_error'if isinstance(exc,ValueError)else'provider_error'
 return {'status':status,'failure_stage':stage,'provider_error_type':type(exc).__name__}

def detector_entities(prediction,source):
 from custom_detector import entities_from_rows,RAW_CLASSES
 rows=entities_from_rows(prediction.boxes.xyxy.tolist(),prediction.boxes.cls.tolist(),prediction.boxes.conf.tolist(),RAW_CLASSES,list(reversed(prediction.orig_shape)),source)
 for index,row in enumerate(rows,1):row.update(id='custom-'+str(index),origin_model='Custom YOLO11m')
 return rows

def direct_fixture(file,question,task,observation,config,output,seconds):
 """Registered custom specialist answer without unrelated segmentation/OCR."""
 import uuid
 seed={'status':'not_run','answer':None,'unit':None,'task':task,'input_kind':'raster','source_sha256':sha(file),'evidence':[],'warnings':[],'route':'direct-specialist-preparation'}
 result=apply(seed,observation,config)
 if result['status']!='success':return None
 folder=Path(output)/'direct-custom-specialist';folder.mkdir(exist_ok=True,parents=True);bundle=folder/'evidence.json';projection=folder/('query-'+hashlib.sha256(json.dumps([question,task],sort_keys=True).encode()).hexdigest()+'.json')
 if not bundle.exists():write_json(bundle,{'facts':observation,'source_sha256':seed['source_sha256'],'configuration':config,'shared_processing':{'cache_hit':observation['execution'].get('cache_hit',False),'note':'Shared specialist observations; unrelated models are not run'}})
 write_json(projection,{'evidence':result['evidence'],'task':task,'question':question})
 cached=observation['execution'].get('cache_hit',False)
 result.update(request_id=uuid.uuid4().hex,question=question,device=observation['execution']['device'],timing={'total_seconds':seconds,'cache_hit':cached,'model_loading_seconds':0,'inference_seconds':0 if cached else observation['execution']['inference_seconds']},stage_timings={},shared_evidence={'path':str(bundle),'sha256':sha(bundle),'key':folder.name},question_evidence={'path':str(projection),'sha256':sha(projection)},paired_timing={'shared_preprocessing_seconds_charged':0 if cached else seconds,'shared_cache_lookup_seconds':seconds if cached else 0,'local_answer_seconds':0,'note':'Direct custom specialist; no unrelated OCR/segmentation and no saved answer lookup'})
 return result

def install(runtime,config,selector_model=None):
 import torch,demo_gpu
 from ultralytics import YOLO
 from custom_detector import RAW_CLASSES,WEIGHT_SHA256,weights_path
 weights=Path('/weights/campaign-assets-v1/floorplan_yolo11m.pt')
 if not weights.is_file():weights=weights_path()
 if sha(weights)!=WEIGHT_SHA256:raise ValueError('Candidate custom checkpoint checksum mismatch')
 runtime.custom=YOLO(str(weights));runtime.custom.model.to('cuda:0');runtime.loads['custom_yolo']=1
 if list(runtime.custom.names.values())!=RAW_CLASSES:raise ValueError('Candidate class-map mismatch')
 def observe(file):
  source=sha(file);settings={'version':'overnight-yolo-observations-v1','imgsz':1024,'conf':.05,'iou':.7,'max_det':500,'preprocessing':'Ultralytics YOLO letterbox; original pixel XYXY'};key=hashlib.sha256(json.dumps([source,WEIGHT_SHA256,settings],sort_keys=True).encode()).hexdigest();path=CACHE_ROOT/'campaign-custom'/(key+'.json')
  if path.exists():
   cached=json.loads(path.read_text());cached['execution']['cache_hit']=True;return cached
  before=runtime.gpu_admission();start=time.perf_counter();devices=set();hook=runtime.custom.model.register_forward_pre_hook(lambda m,args:devices.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
  try:
   from qa.common import inference_lock
   with inference_lock():r=runtime.custom.predict(str(file),device=0,imgsz=1024,conf=.05,iou=.7,max_det=500,verbose=False,save=False)[0];torch.cuda.synchronize()
  finally:hook.remove()
  if 'cuda:0'not in devices:raise RuntimeError('Custom executing CUDA tensor not observed')
  ex={'model':'Custom YOLO11m','device':'cuda:0','observed_tensor_devices':sorted(devices),'worker_id':runtime.worker_id,'load_counts':dict(runtime.loads),'cache_hit':False,'inference_seconds':time.perf_counter()-start,'peak_gpu_memory_bytes':torch.cuda.max_memory_allocated(),'gpu_before':before,'gpu_after':runtime.resource_sample()};demo_gpu._last.append(ex);result={'source_sha256':source,'status':'success','image_size':list(reversed(r.orig_shape)),'model':{'name':'Supplied YOLO11m','weight_sha256':WEIGHT_SHA256,'classes':RAW_CLASSES},'settings':settings,'execution':ex,'cache_key':key,'entities':detector_entities(r,source)};write_json(path,result);return result
 semantic_model=selector_model.get('semantic')if selector_model and 'semantic'in selector_model else selector_model
 opening_model=selector_model.get('opening')if selector_model and 'semantic'in selector_model else None
 original_local=runtime.app.paired.local
 def local(file,question,sample_id=None,progress=None):
  from qa.router import route
  task=route(question)
  if Path(file).suffix.lower()in ['.png','.jpg','.jpeg']and task.get('operation')=='count'and task.get('target')in config.get('targets',{})and not task.get('filters')and task.get('scope')!='model':
   started=time.perf_counter();observation=observe(file);result=direct_fixture(file,question,task,observation,config,runtime.app.paired.output,time.perf_counter()-started)
   if result is not None:return result
  r=original_local(file,question,sample_id,progress);task=r.get('task',{});target=task.get('target')
  if Path(file).suffix.lower()=='.pdf'and r.get('status')!='success'and task.get('operation')in ['area','count']and target in ['room','apartment']:
   from .pdf_quantities import recover
   from qa.tools import pdf_answer
   try:
    facts=recover(file);proposal=pdf_answer(facts,task,question)
    if proposal['status']=='success':r.update(proposal,route='pdf.prefixed-native-room-evidence.campaign-v3',closed_room_geometry_recovery=facts['closed_room_geometry_recovery'])
   except Exception:pass
  task=r.get('task',{});target=task.get('target')
  if r.get('input_kind')!='raster'or task.get('operation')!='count'or task.get('filters')or task.get('scope')=='model':return r
  if target in config.get('targets',{}):return apply(r,observe(file),config)
  if target in config.get('ensemble',{}):
   from v2.structural import parse
   rt=parse(file);custom=observe(file);e=instances(rt['entities'],custom['entities'],target,config['ensemble'][target]);r=copy.deepcopy(r);r['previous_local']={k:copy.deepcopy(r.get(k))for k in ['answer','evidence','route','status']};r.update(status='success',answer=len(e),unit='count',evidence=e,route='raster.instance-corroboration.campaign-v1',postprocessing={'profile':config['ensemble'][target]},calculation_trace=[{'operation':'count_unique_included_entities','ids':[x['id']for x in e],'value':len(e)}]);return r
  return r
 runtime.app.paired.local=local;original_final=runtime.app.paired.hybrid
 def expert(local,reason):return {'status':local['status'],'answer':local.get('answer'),'unit':local.get('unit'),'evidence_ids':[e['id']for e in local.get('evidence',[])],'explanation':reason,'provider_invoked':False,'provider_attempts':0,'supporting_tool':local.get('route'),'chosen_route':'development-validated-specialist','route_reason':reason,'generation':[],'timing':{'additional_gemini_seconds':0}}
 def final(file,question,local):
  task=local.get('task',{});target=task.get('target')
  if local.get('status')=='success'and (local.get('route')=='raster.custom-yolo.campaign-v1'or(local.get('route')=='raster.instance-corroboration.campaign-v1'and not opening_model)):return expert(local,'Existing specialist selected by drawing-group development validation; unique included source instances determine the count')
  if not semantic_model or local.get('input_kind')!='raster'or task.get('operation')!='count'or task.get('filters')or target not in config.get('semantic_review_targets',[]):return original_final(file,question,local)
  from .review import request
  from .selector import select
  from v2.ocr import parse as ocr_parse
  from v3.raster import parse as room_parse
  from v2.structural import parse as structural_parse
  start=time.perf_counter();generation=[];attempts=0;stage='additional_local_evidence';operation='live-grounded-review:'+__import__('uuid').uuid4().hex
  def count_attempts():
   from deploy.modal.presenter_budget import PresenterLedger
   with PresenterLedger().connect()as c:return c.execute('SELECT COUNT(*) FROM attempts WHERE operation=?',(operation,)).fetchone()[0]
  def provider(*args,**kwargs):
   from v2.gemini import generate
   kwargs['operation']=operation;return generate(*args,**kwargs)
  try:
   rooms=room_parse(file);rt=structural_parse(file);custom=observe(file);ocr=ocr_parse(file);prep=time.perf_counter()-start
   stage='provider_review';review=request(file,[local],[('custom_yolo',custom),('rtdetr',rt),('rooms',rooms)],ocr['words'],model=config.get('review_model','gemini-3-flash-preview'),provider=provider);attempts=count_attempts();stage='proposal_validation_and_selection'
   chosen=select(local,review,ocr['words'],custom['image_size'],semantic_model)
   if target in ['door','window']and opening_model:
    from .openings import choose
    chosen=choose(local,review,ocr['words'],custom['image_size'],rt,custom,opening_model)
   source=chosen.get('opening_selector',chosen.get('selector',{})).get('selected','local');generation=[{'model':review['model'],'usage':review['usage'],'reserved_usd':review['reserved_usd'],'prompt_sha256':review['prompt_sha256']}];ids=[e['id']for e in chosen.get('evidence',[])];regions=[]
   if source=='review':regions=[{k:v for k,v in e.items()if k!='score'}for e in chosen['evidence']]
   elif source!='local':
    cumulative=local.setdefault('cumulative_evidence',{});cumulative.setdefault('evidence',[]).extend(copy.deepcopy(chosen['evidence']))
   return {'status':chosen['status'],'answer':chosen.get('answer'),'unit':chosen.get('unit'),'evidence_ids':ids,'explanation':'Selected '+source+' evidence after cumulative visual/OCR review; inspect highlighted source regions.','provider_invoked':True,'provider_attempts':attempts,'model_proposed_regions':regions,'selector':chosen.get('opening_selector',chosen.get('selector')),'chosen_route':'grounded-proposal-selector','route_reason':'Only existing model/OCR/visual-region proposals are eligible; no count averaging or reference lookup','generation':generation,'timing':{'additional_gemini_seconds':review['generation_seconds'],'additional_local_evidence_seconds':prep,'total_review_seconds':time.perf_counter()-start},'scope_limitations':'New localization is model-proposed, not spatial ground truth. Offline development review batched available questions per drawing; single live-question review context can differ.'}
  except Exception as exc:

   try:attempts=count_attempts()
   except Exception:pass
   return {**review_failure(exc,stage),'answer':None,'unit':None,'evidence_ids':[],'explanation':'Cumulative review unavailable ('+type(exc).__name__+'); completed Local evidence retained.','provider_invoked':attempts>0,'provider_attempts':attempts,'generation':generation,'timing':{'additional_gemini_seconds':time.perf_counter()-start}}
 runtime.app.paired.hybrid=final
 return {'custom_weight_sha256':WEIGHT_SHA256,'selector_enabled':bool(selector_model),'configuration':config}
