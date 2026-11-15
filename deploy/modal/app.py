"""Stable deployment entrypoint: legacy rollback or explicit versioned event role."""
import os,json,time,subprocess,sys
from pathlib import Path
import modal
from deploy.modal.base_image import image,weights,REV,VERSION,GPU_APP,ROLE_CONFIG
app=modal.App(os.environ.get('FLOORHAWK_APP_NAME','floorhawk-demo'))
jobs=modal.Volume.from_name('floorhawk-jobs',create_if_missing=True)
state=modal.Dict.from_name('floorhawk-control-v1',create_if_missing=True)
@app.function(serialized=False,image=image,volumes={'/weights':weights},timeout=120,cpu=1,memory=1024,max_containers=1,min_containers=0)
def verify_assets():
 import hashlib
 from pathlib import Path
 m=json.loads((Path('/weights')/VERSION/'assets.json').read_text());bad=[]
 for r in m['models']:
  p=Path('/weights')/VERSION/r['filename'];h=hashlib.sha256(p.read_bytes()).hexdigest()
  if h!=r['sha256']or p.stat().st_size!=r['size']:bad.append(r['filename'])
 if bad:raise RuntimeError('Asset verification failed: '+str(bad))
 return {'release':REV,'asset_version':VERSION,'verified_files':len(m['models']),'bytes':sum(r['size']for r in m['models'])}
@app.function(serialized=False,image=image,gpu=None if GPU_APP else 'T4',secrets=[modal.Secret.from_name('floorhawk-gemini')],volumes={'/weights':weights,'/jobs':jobs},timeout=480,cpu=2,memory=8192,max_containers=1,min_containers=0,scaledown_window=15,retries=0)
def gpu_job(ident):
 import tempfile
 jobs.reload();dest=Path('/jobs/app')/ident
 with tempfile.TemporaryDirectory(prefix='floorhawk-job-')as tmp:
  env=dict(os.environ,PROOFPLAN_CACHE_ROOT=tmp,PROOFPLAN_RESULTS_ROOT='/jobs')
  p=subprocess.Popen([sys.executable,'/opt/floorhawk/deploy/modal/cloud_worker.py',ident],env=env,cwd='/opt/floorhawk')
  start=time.monotonic()
  while p.poll()is None:
   jobs.commit()
   if time.monotonic()-start>420:p.kill();p.wait();break
   time.sleep(1)
  if p.returncode:
   path=dest/'job.json';j=json.loads(path.read_text());j.update(status='failed',stage='Cloud worker stopped',error='Bounded cloud worker failed or timed out; inspect saved progress',progress=0);path.write_text(json.dumps(j))
  jobs.commit()
  from deploy.modal.security import Controls
  try:Controls(state,'').complete(ident,json.loads((dest/'job.json').read_text())['status'])
  except Exception:pass # Fail closed: polling can finalize; orphan remains active rather than bypassing quota.
 return {'job_id':ident,'release':REV,'status':json.loads((dest/'job.json').read_text())['status']}
@app.function(serialized=False,image=image,volumes={'/weights':weights,'/jobs':jobs},secrets=[modal.Secret.from_name('floorhawk-access')],timeout=120,cpu=1,memory=4096,max_containers=1,min_containers=0,scaledown_window=30)
@modal.concurrent(max_inputs=20)
@modal.asgi_app(label=os.environ.get('FLOORHAWK_ENDPOINT_LABEL','web'))
def web():
 os.chdir('/opt/floorhawk');sys.path.insert(0,'/opt/floorhawk')
 from deploy.modal.gateway import create_gateway
 return create_gateway(state,jobs,lambda ident:(modal.Function.from_name(GPU_APP,'gpu_job').spawn(ident)if GPU_APP else gpu_job.spawn(ident)),REV)
@app.local_entrypoint()
def main():print(verify_assets.remote())

# No event role is selected implicitly. Existing rollback commands retain legacy behavior.
if ROLE_CONFIG.get('role')or os.environ.get('FLOORHAWK_EVENT_ROLE'):
 if ROLE_CONFIG.get('role')=='evaluation':
  from campaign.final_worker import app as event_app
 else:
  if modal.is_local()and ROLE_CONFIG.get('prepare_assets')and 'deploy'in sys.argv:
   from deploy.modal.prepare_event import prepare
   prepare(ROLE_CONFIG)
  from deploy.modal.event import app as event_app
 app=event_app
