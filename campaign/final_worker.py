"""Private, scale-to-zero frozen Local evaluation. Never receives references or keys."""
import os,time,json,base64,hashlib,shutil
from pathlib import Path
import modal
from deploy.modal.base_image import image as base_image,weights,REV,VERSION
from campaign.clock import DEADLINES
from campaign.final_contract import validate_questions
app=modal.App('floorhawk-final-evaluation')
image=base_image.env({'PROOFPLAN_RESULTS_ROOT':'/tmp/floorhawk-final-results','PROOFPLAN_CACHE_ROOT':'/tmp/floorhawk-final-cache'})
@app.cls(serialized=False,image=image,gpu='T4',cpu=2,memory=8192,timeout=90,max_containers=1,min_containers=0,scaledown_window=15,retries=0,volumes={'/weights':weights})
class FinalWorker:
 @modal.enter()
 def initialize(self):
  if time.time()>=DEADLINES['evaluate']-30:raise TimeoutError('Final worker startup closed before campaign stop')
  os.chdir('/opt/floorhawk')
  from deploy.modal.presenter_runtime import Runtime
  self.runtime=Runtime();cfg=json.loads(Path('/opt/floorhawk/config/overnight-candidate.json').read_text());model=Path('/weights')/cfg['selector_asset']
  if hashlib.sha256(model.read_bytes()).hexdigest()!=cfg['selector_sha256']:raise ValueError('Frozen selector checksum mismatch')
  from campaign.live_adapter import install
  install(self.runtime,cfg,json.loads(model.read_text()))
  import v2.gemini
  def blocked(*args,**kwargs):raise RuntimeError('Provider calls prohibited in frozen Local evaluation')
  v2.gemini.generate=blocked;self.runtime.app.paired.provider=blocked;self.sources=0
 @modal.method()
 def ready(self):return dict(self.runtime.readiness(),source_commit=REV,provider_calls_allowed=False,sources=self.sources)
 @modal.method()
 def evaluate(self,source_hash,extension,encoded,questions,release,deadline):
  validate_questions(questions)
  if release!=REV:raise ValueError('Frozen release mismatch')
  if time.time()<DEADLINES['optimize']or time.time()+90>min(deadline,DEADLINES['evaluate']):raise TimeoutError('Frozen evaluation admission window closed')
  if extension not in ['.png','.jpg','.jpeg','.pdf','.ifc']:raise ValueError('Unsupported source format')
  raw=base64.b64decode(encoded,validate=True)
  if len(raw)>20*1024**2 or hashlib.sha256(raw).hexdigest()!=source_hash:raise ValueError('Source bound/hash mismatch')
  from runtime_paths import CACHE_ROOT,RESULTS_ROOT
  from qa.common import write_json
  import torch,demo_gpu
  started=time.perf_counter();self.sources+=1;shutil.rmtree(CACHE_ROOT,ignore_errors=True);CACHE_ROOT.mkdir();(CACHE_ROOT/'qa').mkdir();self.runtime.app.pipeline.base.memory.clear();self.runtime.app.paired.documents.clear();folder=RESULTS_ROOT/REV/source_hash;folder.mkdir(parents=True,exist_ok=True);source=folder/('source'+extension);source.write_bytes(raw);self.runtime.app.paired.output=folder/'bundles';self.runtime.app.paired.output.mkdir(exist_ok=True);unsupported=None
  if extension in ['.png','.jpg','.jpeg']:
   from PIL import Image
   with Image.open(source)as im:
    if im.width*im.height>8_000_000:unsupported='Frozen evaluation8MP source bound; no reduced-preview-only substitute'
  elif extension=='.pdf':
   import pymupdf
   with pymupdf.open(source)as doc:
    if len(doc)>20:unsupported='Frozen evaluation20page bound'
  elif len(raw)>10*1024**2 or raw.count(b'=IFC')>100000:unsupported='Frozen IFC complexity bound'
  rows=[];torch.cuda.reset_peak_memory_stats()
  for q in questions:
   if time.time()+8>min(deadline,DEADLINES['evaluate'])or time.perf_counter()-started>75:break
   began=time.perf_counter();demo_gpu._last.clear()
   try:
    result={'status':'unsupported','answer':None,'unit':None,'evidence':[],'warnings':[unsupported],'coverage':{'complete':False}}if unsupported else self.runtime.app.paired.local(source,q['question'],sample_id=None)
   except Exception as exc:result={'status':'failed','answer':None,'unit':None,'evidence':[],'error':type(exc).__name__+': '+str(exc)[:240]}
   result.update(sample_id=q['sample_id'],question=q['question'],source_sha256=source_hash,execution_mode='frozen-local-evaluation',live_execution=list(demo_gpu._last),evaluation_query_seconds=time.perf_counter()-began,source_commit=REV);rows.append(result)
  observations=[];bytes_=0
  for p in CACHE_ROOT.rglob('*.json'):
   size=p.stat().st_size
   if bytes_+size>32*1024**2:continue
   try:data=json.loads(p.read_text())
   except ValueError:continue
   if isinstance(data,dict)and data.get('source_sha256')==source_hash:observations.append({'relative_path':str(p.relative_to(CACHE_ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'json_text':p.read_text()});bytes_+=size
  return {'source_sha256':source_hash,'source_commit':REV,'rows':rows,'observations':observations,'source_seconds':time.perf_counter()-started,'resident':self.runtime.readiness(),'complete':len(rows)==len(questions),'provider_attempts':0,'limits':'Local frozen candidate only; observations reused within source, not cold per-question inference. No provider credentials mounted.'}
