"""Dedicated authenticated resident presenter. Does not deploy/update public app."""
import os,sys,time,json
from pathlib import Path
import modal
from deploy.modal.app import image as shared_image,weights,REV,VERSION
app=modal.App('floorhawk-presenter');jobs=modal.Volume.from_name('floorhawk-presenter-jobs',create_if_missing=True);state=modal.Dict.from_name('floorhawk-presenter-control-v1',create_if_missing=True)
image=shared_image.env({'FLOORHAWK_PRESENTER':'1','FLOORHAWK_GALLERY_STORE':'floorhawk-presenter-gallery-v1','FLOORHAWK_GALLERY_ROOT':'/weights/presenter-gallery-v1','PROOFPLAN_RESULTS_ROOT':'/presenter-jobs','PROOFPLAN_CACHE_ROOT':'/tmp/floorhawk-presenter-cache'})
@app.cls(image=image,gpu='T4',cpu=2,memory=8192,timeout=480,max_containers=1,min_containers=1,scaledown_window=120,volumes={'/weights':weights,'/presenter-jobs':jobs},secrets=[modal.Secret.from_name('floorhawk-gemini')])
class Resident:
 @modal.enter()
 def initialize(self):
  os.chdir('/opt/floorhawk');sys.path.insert(0,'/opt/floorhawk');from deploy.modal.presenter_runtime import Runtime
  self.runtime=Runtime(publish=jobs.commit)
 @modal.method()
 def ready(self):return self.runtime.readiness()
 @modal.method()
 def run(self,ident):
  jobs.reload();result=self.runtime.run(ident);jobs.commit()
  from deploy.modal.presenter_controls import PresenterControls
  PresenterControls(state,'').complete(ident,result);return {'job_id':ident,'status':result,'resident':self.runtime.readiness()}
@app.function(image=image,cpu=1,memory=4096,max_containers=1,min_containers=0,timeout=120,volumes={'/weights':weights,'/presenter-jobs':jobs},secrets=[modal.Secret.from_name('floorhawk-presenter-access')])
@modal.concurrent(max_inputs=20)
@modal.asgi_app(label='presenter')
def web():
 os.chdir('/opt/floorhawk');sys.path.insert(0,'/opt/floorhawk');from deploy.modal.gateway import create_gateway
 resident=Resident()
 return create_gateway(state,jobs,lambda ident:resident.run.spawn(ident),REV)
@app.local_entrypoint()
def main():print(Resident().ready.remote())
