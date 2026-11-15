from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""One bounded/cancellable geometry subprocess; independent of inference workers."""
import threading,subprocess,time,json,os,signal,sys
from pathlib import Path
from qa.common import ROOT,write_json
from v2.supervisor import Admission,sample
from .ifc_geometry import key,CACHE
class Jobs:
 def __init__(self):self.lock=threading.Lock();self.jobs={};self.processes={}
 def status(self,source,start=False):
  source=Path(source);k=key(source);folder=CACHE/k;meta=folder/'metadata.json'
  if meta.exists():return dict(json.loads(meta.read_text()),cache_key=k,glb_url=None)
  if k in self.jobs:return self.jobs[k]
  if not start:return{'status':'not_precomputed','cache_key':k,'note':'Model geometry not precomputed; recorded answer remains available'}
  with self.lock:
   if any(j.get('status')in['queued','converting']for j in self.jobs.values()):return{'status':'busy','note':'One geometry conversion at a time; retry after current conversion'}
   self.jobs[k]={'status':'queued','cache_key':k,'note':'CPU geometry conversion only, no inference'};threading.Thread(target=self.run,args=(source,k),daemon=True).start()
  return self.jobs[k]
 def run(self,source,k):
  process=None;admit=Admission();started=time.monotonic();log=RESULTS_ROOT/'inspection'/('geometry-'+k+'.jsonl');env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
  try:
   if admit.check(sample(gpu=False))!='admit':raise RuntimeError('Resource admission paused')
   self.jobs[k]['status']='converting';process=subprocess.Popen([sys.executable,'-m','inspection.ifc_geometry','--source',str(source)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);self.processes[k]=process;paused=False
   with log.open('a')as f:
    while process.poll()is None:
     s=sample(process.pid,gpu=False);decision=admit.check(s);f.write(json.dumps(dict(s,decision=decision))+'\n');f.flush()
     if time.monotonic()-started>120 or decision in ['shed','disk-pressure','telemetry-unavailable']:raise RuntimeError('Geometry stopped on resource/time limit')
     if self.jobs[k]['status']=='cancelled':raise RuntimeError('Geometry cancelled')
     if decision=='pause'and not paused:os.killpg(process.pid,signal.SIGSTOP);paused=True
     elif decision=='admit'and paused:os.killpg(process.pid,signal.SIGCONT);paused=False
     time.sleep(.5)
   if process.returncode:raise RuntimeError('Geometry conversion failed; recorded answer retained')
   self.jobs[k]={'status':'ready','cache_key':k}
  except Exception as e:self.jobs[k]={'status':'cancelled'if self.jobs.get(k,{}).get('status')=='cancelled'else'failed','cache_key':k,'note':str(e)}
  finally:
   if process and process.poll()is None:os.killpg(process.pid,signal.SIGCONT);os.killpg(process.pid,signal.SIGTERM)
   self.processes.pop(k,None)
 def cancel(self,source):
  k=key(source)
  if k in self.jobs and self.jobs[k]['status']in['queued','converting']:self.jobs[k]['status']='cancelled'
  return{'status':self.jobs.get(k,{}).get('status','not_running')}
JOBS=Jobs()
