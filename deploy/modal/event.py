"""One versioned resident backend, isolated presenter/judges/public admission and GPU."""
import os,json,sys,hashlib,hmac,time
from pathlib import Path
import modal
from deploy.modal.base_image import image as base_image,weights,REV,VERSION,ROLE_CONFIG
ROLE=os.environ.get('FLOORHAWK_EVENT_ROLE')or ROLE_CONFIG.get('role','candidate')
ROLES={'presenter':{'app':'floorhawk-presenter','label':'presenter','jobs':'floorhawk-presenter-jobs','root':'/presenter-jobs','control':'floorhawk-presenter-control-v1','warm':1,'secret':'floorhawk-presenter-access'},'judges':{'app':'floorhawk-judges','label':'judges','jobs':'floorhawk-judges-jobs','root':'/judges-jobs','control':'floorhawk-judges-control-v1','warm':1,'secret':'floorhawk-presenter-access'},'public':{'app':'floorhawk-demo','label':'web','jobs':'floorhawk-jobs','root':'/jobs','control':'floorhawk-control-v1','warm':0,'secret':'floorhawk-access'},'candidate':{'app':'floorhawk-overnight-candidate','label':'overnight-candidate','jobs':'floorhawk-candidate-jobs','root':'/candidate-jobs','control':'floorhawk-candidate-control-v1','warm':0,'secret':'floorhawk-presenter-access'}}
if ROLE not in ROLES:raise ValueError('Unregistered event deployment role')
R=ROLES[ROLE];app=modal.App(R['app']);jobs=modal.Volume.from_name(R['jobs'],create_if_missing=True);state=modal.Dict.from_name(R['control'],create_if_missing=True)
image=base_image.env({'FLOORHAWK_EVENT_ROLE':ROLE,'FLOORHAWK_PRESENTER':'0'if ROLE=='public'else'1','FLOORHAWK_GALLERY_STORE':'floorhawk-presenter-gallery-v1','FLOORHAWK_GALLERY_ROOT':'/weights/presenter-gallery-v1','PROOFPLAN_RESULTS_ROOT':R['root'],'PROOFPLAN_CACHE_ROOT':'/tmp/floorhawk-event-'+ROLE})
@app.cls(serialized=False,image=image,gpu='T4',cpu=(2,2),memory=(8192,8192),timeout=480,max_containers=1,min_containers=R['warm'],scaledown_window=120,retries=0,volumes={'/weights':weights,R['root']:jobs},secrets=[modal.Secret.from_name('floorhawk-gemini')])
class Resident:
 @modal.enter()
 def initialize(self):
  boot_started=time.perf_counter()
  os.chdir('/opt/floorhawk');sys.path.insert(0,'/opt/floorhawk')
  from deploy.modal.presenter_runtime import Runtime
  manifest=json.loads((Path('/weights')/VERSION/'assets.json').read_text());verified=[]
  for row in manifest['models']:
   asset=Path('/weights')/VERSION/row['filename']
   if asset.stat().st_size!=row['size']or hashlib.sha256(asset.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Runtime asset checksum mismatch')
   verified.append(row['filename'])
  self.assets_verified=len(verified)
  asset_seconds=time.perf_counter()-boot_started
  self.runtime=Runtime(publish=jobs.commit);p=Path('/opt/floorhawk/config/overnight-candidate.json');custom_started=time.perf_counter()
  if p.is_file():
   cfg=json.loads(p.read_text());model=None
   if cfg.get('selector_sha256'):
    model_path=Path('/weights')/cfg['selector_asset']
    if hashlib.sha256(model_path.read_bytes()).hexdigest()!=cfg['selector_sha256']:raise ValueError('Selector asset checksum mismatch')
    model=json.loads(model_path.read_text())
   from campaign.live_adapter import install
   self.candidate=install(self.runtime,cfg,model)
  self.runtime.extra_startup={'asset_verification_seconds':asset_seconds,'custom_initialization_seconds':time.perf_counter()-custom_started,'complete_initialization_seconds':time.perf_counter()-boot_started,'note':'Worker entrypoint measurement; platform scheduling/image startup are not included'}
  import v2.gemini as gemini
  original_generate=gemini.generate
  def guarded_generate(*args,**kwargs):
   active=state.get('admission-state-v1',{})
   if not active.get('gemini')or not getattr(self,'job_review_enabled',True):raise gemini.ProviderBlocked('Role Gemini stop switch is off; Local result retained')
   return original_generate(*args,**kwargs)
  gemini.generate=guarded_generate;self.runtime.app.paired.provider=guarded_generate
 @modal.method()
 def ready(self):return dict(self.runtime.readiness(),role=ROLE,release=REV,verified_asset_files=self.assets_verified,resource_limits={'cpu_request_cores':2,'cpu_limit_cores':2,'memory_request_mib':8192,'memory_limit_mib':8192,'gpu_max_workers':1})
 @modal.method()
 def run(self,ident):
  jobs.reload();job=json.loads((Path(R['root'])/'app'/ident/'job.json').read_text());self.job_review_enabled=job.get('gemini_enabled_at_submission',True);status=self.runtime.run(ident);jobs.commit()
  from deploy.modal.presenter_controls import PresenterControls
  from deploy.modal.security import Controls
  (Controls if ROLE=='public'else PresenterControls)(state,'').complete(ident,status);return {'job_id':ident,'status':status,'role':ROLE,'resident':self.runtime.readiness()}
@app.function(serialized=False,image=image,cpu=(1,1),memory=(4096,4096),max_containers=2 if ROLE=='public' else 1,min_containers=0,timeout=120,volumes={'/weights':weights,R['root']:jobs},secrets=[modal.Secret.from_name(R['secret'])])
@modal.concurrent(max_inputs=20)
@modal.asgi_app(label=R['label'])
def web():
 os.chdir('/opt/floorhawk');sys.path.insert(0,'/opt/floorhawk')
 if ROLE in['judges','candidate']:
  # Distinct revocable role code and cookie key, derived server-side from existing secret.
  root=os.environ['FLOORHAWK_SESSION_KEY'].encode();code=hmac.new(root,('floorhawk-access-'+ROLE+'-v1').encode(),'sha256').hexdigest();os.environ['FLOORHAWK_ACCESS_HASH']=hashlib.sha256(code.encode()).hexdigest();os.environ['FLOORHAWK_SESSION_KEY']=hmac.new(root,('floorhawk-session-'+ROLE).encode(),'sha256').hexdigest()
 from deploy.modal.gateway import create_gateway
 resident=Resident();return create_gateway(state,jobs,lambda ident:resident.run.spawn(ident),REV)
