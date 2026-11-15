"""Isolated one-job process: fresh extraction, existing CPU tools + CUDA models."""
import os,json,sys,time,base64
from pathlib import Path

def main(ident):
 import demo_gpu
 demo_gpu._enabled=True # Do not install laptop RPC wrappers in a cloud process.
 from qa.raster import CubiParser
 original=CubiParser.parse
 def cuda_parse(self,path):
  import torch
  demo_gpu.release_host_models();self.device='0';observed=set()
  hook=torch.nn.modules.module.register_module_forward_pre_hook(lambda m,args:observed.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
  try:r=original(self,path)
  finally:hook.remove()
  if 'cuda:0'not in observed:raise RuntimeError('No CUDA input tensor observed')
  r['execution']={'device':'cuda:0','model':'CubiCasa5K','observed_tensor_devices':sorted(observed),'executing_pid':os.getpid(),'peak_gpu_memory_bytes':r.get('peak_gpu_memory_bytes'),'cache_hit':False};demo_gpu._last.append(r['execution']);return r
 CubiParser.parse=cuda_parse
 demo_gpu.enabled=lambda:True
 demo_gpu.call=lambda file,model,settings:demo_gpu.host_vision({'model':model,'settings':settings,'image_base64':base64.b64encode(Path(file).read_bytes()).decode()})
 import qa_app
 app=qa_app.Application('cpu');app.samples=[];app.pipeline.set_cloud(True);app.pipeline.local_routing=False
 path=qa_app.STORE/ident/'job.json';job=json.loads(path.read_text());app.jobs[ident]=job;worker_started=time.time();job['_submitted_perf']=time.perf_counter()
 if job.get('mode')=='hybrid':
  import v2.budget,v2.gemini
  from deploy.modal.cloud_budget import CloudLedger
  v2.budget.Ledger=CloudLedger;v2.gemini.Ledger=CloudLedger
  key=os.environ.get('GEMINI_API_KEY')or os.environ.get('GOOGLE_API_KEY')or os.environ.get('API_KEY')
  if key:
   secret=Path(os.environ['PROOFPLAN_CACHE_ROOT'])/'gemini.key';secret.write_text(key);secret.chmod(0o600);os.environ['PROOFPLAN_GEMINI_KEY_FILE']=str(secret)
 app.paired.output=Path('/jobs/app')/ident/'evidence-bundles';app.paired.output.mkdir(exist_ok=True)
 # Publish Local progress to shared storage; the parent commits it while child runs.
 app.execute(ident)
 job=json.loads(path.read_text());job['api_contract']='floorhawk.jobs.v1';job['release']=json.loads(Path('/opt/floorhawk/release.json').read_text());h=job.get('prediction',{}).get('paired',{}).get('hybrid',{});local=job.get('prediction',{}).get('paired',{}).get('local',{});job['cloud_timing']={'queue_and_startup_seconds':max(0,worker_started-job['created']),'worker_seconds':time.time()-worker_started,'total_seconds':time.time()-job['created'],'local':local.get('paired_timing',{}),'gemini':h.get('timing',{}),'note':'Queue and container startup are combined because separately attributable timestamps are unavailable'};job['extraction_policy']='fresh per accepted request; shared only within request';path.write_text(json.dumps(job));app.worker.shutdown(wait=False)
if __name__=='__main__':main(sys.argv[1])
