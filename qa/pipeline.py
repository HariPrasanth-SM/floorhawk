"""Shared answer(file, question) pipeline. No evaluator or benchmark answer imports."""
import collections,json,time,traceback,uuid
from pathlib import Path
from .common import ROOT,CACHE,VERSION,sha,write_json,inference_lock
from .router import route,validate_task
from .tools import pdf_answer,ifc_answer,raster_answer,unsupported

class Pipeline:
 def __init__(self,device='cpu',max_edge=512,vlm_url=None):
  self.device=device;self.max_edge=max_edge;self.vlm_url=vlm_url;self.raster=None;self.memory=collections.OrderedDict();self.hashes={};self.vlm_health=None
  self.sources={p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}
  import hashlib
  self.preprocessing_version=hashlib.sha256(json.dumps({'source':{name:h for name,h in self.sources.items() if name in ('raster.py','pdf.py','ifc.py','common.py')},'max_edge':max_edge,'cubi_revision':'c34440266665a11f4484eb06cd2e4b7d72ad76c1','weights_sha256':'dd20b4e1bf1d670f2125107b079df06958b1ccd36e49a464ab739aeb00b8e7a2'},sort_keys=True).encode()).hexdigest()
 def file_hash(self,path):
  # The on-disk cache identity always uses bytes, never a filename-derived answer.
  path=Path(path);key=(str(path.resolve()),path.stat().st_size,path.stat().st_mtime_ns)
  if key not in self.hashes:self.hashes[key]=sha(path)
  return self.hashes[key]
 def facts(self,path):
  path=Path(path);h=self.file_hash(path);key=h+'-'+self.preprocessing_version+('-cuda0' if self.device=='0' and path.suffix.lower() in ('.png','.jpg','.jpeg') else '');
  from demo_gpu import enabled,_last
  if enabled() and path.suffix.lower() in ('.png','.jpg','.jpeg'):key+='-host-auto-v1'
  cache=CACHE/(key+'.json');started=time.perf_counter()
  if key in self.memory:
   self.memory.move_to_end(key)
   if self.memory[key].get('execution'):_last.append(dict(self.memory[key]['execution'],cache_hit=True))
   return self.memory[key],True,time.perf_counter()-started,cache
  if cache.exists():data=json.loads(cache.read_text());cached=True
  else:
   cached=False;t=time.perf_counter()
   with inference_lock():
    suffix=path.suffix.lower()
    if suffix=='.pdf':
     from .pdf import parse_pdf
     data=parse_pdf(path)
    elif suffix=='.ifc':
     from .ifc import parse_ifc
     data=parse_ifc(path)
    elif suffix in ('.png','.jpg','.jpeg'):
     from .raster import CubiParser
     if self.raster is None:self.raster=CubiParser(self.device,self.max_edge)
     data=self.raster.parse(path)
     maps=data.pop('_maps')
     from PIL import Image
     for name,array in zip(['rooms','icons'],maps):Image.fromarray(array).save(CACHE/(key+'-'+name+'.png'))
    else:raise ValueError('Supported inputs are PNG, JPEG, PDF and IFC')
   data.update(source_sha256=h,preprocessing_version=self.preprocessing_version,parse_seconds=time.perf_counter()-t,device=data.get('execution',{}).get('device',self.device) if data['kind']=='raster' else 'cpu');write_json(cache,data)
  if data.get('kind')=='ifc' and 'unit_policy' not in data:
   import ifcopenshell
   unit_model=ifcopenshell.open(str(path));declared=set()
   for assignment in unit_model.by_type('IfcUnitAssignment'):
    declared.update(getattr(unit,'UnitType','') for unit in assignment.Units)
   overrides=[q.id() for q in unit_model.by_type('IfcPhysicalSimpleQuantity') if getattr(q,'Unit',None) is not None]
   data['unit_policy']={'declared_project_units':sorted(declared),'explicit_quantity_unit_override_ids':overrides,'policy':'Use explicit project SI scales only. Missing dimensions or per-quantity overrides abstain rather than silently using the wrong unit.'}
   write_json(cache,data)
  if cached and data.get('execution'):_last.append(dict(data['execution'],cache_hit=True))
  self.memory[key]=data
  while len(self.memory)>4:self.memory.popitem(last=False)
  return data,cached,time.perf_counter()-started,cache
 def answer(self,file,question,sample_id=None,progress=None):
  started=time.perf_counter();result={'request_id':uuid.uuid4().hex,'sample_id':sample_id,'status':'failed','answer':None,'unit':None,'evidence':[],'warnings':[],'device':self.device,'settings':{'max_edge':self.max_edge,'preprocessing_version':self.preprocessing_version,'vlm_url':self.vlm_url},'route':'unresolved','tool_revisions':{'pipeline':VERSION},'source_revision':self.sources,'peak_gpu_memory_bytes':None}
  try:
   path=Path(file)
   if not isinstance(question,str) or not question.strip() or len(question)>4000:raise ValueError('Enter a question between 1 and 4000 characters')
   task=route(question);result.update(task=task,question=question,source_sha256=self.file_hash(path))
   if progress:progress('Extracting local drawing evidence',0,1)
   facts,cached,parse_time,cache=self.facts(path);query_start=time.perf_counter()
   result['route']={'pdf':'pdf.native','ifc':'ifc.structured','raster':'raster.official-cubicasa'}[facts['kind']]
   if progress:progress('Querying extracted entities',1,1)
   if (task['operation']=='unknown' or task['target']=='unknown') and self.vlm_url:
    from .vlm_client import LocalVLM
    client=LocalVLM(self.vlm_url);health=client.health()
    if health.get('ready'):
     routed=client.route(question)
     if routed.get('status')=='success':task=validate_task(routed['task']);result['task']=task
   tool={'pdf':pdf_answer,'ifc':ifc_answer,'raster':raster_answer}[facts['kind']]
   answer=unsupported('Question could not be mapped to a registered operation/target; use a supported template or the optional local interpretation worker.') if task['operation']=='unknown' or task['target']=='unknown' else tool(facts,task,question)
   result.update(answer);result['warnings']=facts.get('warnings',[])+answer.get('warnings',[])
   for e in result['evidence']:e['source_sha256']=facts['source_sha256']
   result['tool_revisions'].update({facts.get('tool','CubiCasa5K'):facts.get('model',{}).get('revision',self.preprocessing_version)})
   if facts.get('model'):result['model']=facts['model'];result['preprocessing']=facts['preprocessing']
   result['peak_gpu_memory_bytes']=facts.get('peak_gpu_memory_bytes');result['facts_cache_key']=cache.stem;result['input_kind']=facts['kind'];result['facts_generation_device']=facts.get('device','not recorded in earlier facts; consult source batch run.json')
   result['timing']={'cache_hit':cached,'first_file_parse_seconds':0 if cached else facts['parse_seconds'],'cache_read_seconds':parse_time if cached else 0,'query_seconds':time.perf_counter()-query_start,'model_loading_seconds':0 if cached else facts.get('timing',{}).get('model_loading_seconds',0),'inference_seconds':0 if cached else facts.get('timing',{}).get('inference_seconds',0),'cold_model':False if cached else facts.get('timing',{}).get('cold_model',False)}
   if result['status']!='success' and self.vlm_url:
    from .vlm_client import LocalVLM
    client=LocalVLM(self.vlm_url)
    health=client.health()
    if health.get('ready'):
     proposed=client.answer(path,question,task,facts)
     if proposed['status']=='success':
      result['alternatives']=[{'route':result['route'],'status':result['status'],'warnings':result['warnings']}];result.update(proposed);result['warnings'].append('Direct VLM estimate is ungrounded by instance boxes; review required.')
    else:result['warnings'].append('VLM route blocked: '+str(health.get('error',health.get('status'))));result['vlm_status']='blocked'
   elif result['status']!='success':result['vlm_status']='disabled'
   # Physical units are normalized by tools; explicit smaller length units are converted here.
   requested=task.get('requested_unit')
   if result['status']=='success' and result['unit']=='m' and requested in ('mm','cm'):
    factor={'mm':1000,'cm':100}[requested];result['answer']*=factor;result['unit']=requested;result['calculation_trace'].append({'operation':'unit_conversion','from':'m','to':requested,'factor':factor})
  except Exception as exc:result.update(status='failed',error=str(exc),warnings=[str(exc)],traceback=traceback.format_exc())
  result.setdefault('timing',{})['total_seconds']=time.perf_counter()-started;result['latency_seconds']=result['timing']['total_seconds']
  return result

def answer(file,question,**kwargs):return Pipeline().answer(file,question,**kwargs)
