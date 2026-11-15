from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""One-second system/owned telemetry, fail-closed admission and owned-tree shedding.
Host launch uses an aggregate systemd scope when available; this monitor never kills
unrelated processes. GPU utilization requires sustained pressure, memory is immediate.
"""
import argparse,json,os,signal,subprocess,sys,time,uuid
from pathlib import Path
import psutil
from .policy import ROOT,STATE,POLICY

def sample(root_pid=None,gpu=True):
 m=psutil.virtual_memory();d=psutil.disk_usage(ROOT);result={'time':time.time(),'cpu_percent':psutil.cpu_percent(),'ram_used_percent':100*(1-m.available/m.total),'ram_available_bytes':m.available,'disk_free_bytes':d.free,'gpu_available':False}
 if gpu:
  try:
   p=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,check=True)
   used,total,util=map(float,p.stdout.splitlines()[0].split(','));result.update(gpu_available=True,gpu_memory_percent=100*used/total,gpu_used_mib=used,gpu_total_mib=total,gpu_utilization_percent=util)
  except Exception:result['gpu_error']='GPU telemetry unavailable in this context'
 if root_pid:
  try:
   processes=[psutil.Process(root_pid)]+psutil.Process(root_pid).children(recursive=True);result['owned_rss_bytes']=sum(p.memory_info().rss for p in processes if p.is_running());result['owned_cpu_seconds']=sum(sum(p.cpu_times()[:2]) for p in processes if p.is_running());result['owned_pids']=[p.pid for p in processes]
  except psutil.Error:result['owned_pids']=[]
 return result

class Admission:
 def __init__(self):self.paused=False;self.recovery=None;self.gpu_high_since=None
 def check(self,s,require_gpu=False,now=None):
  now=time.time() if now is None else now;r=POLICY['resources']
  if require_gpu and not s.get('gpu_available'):return 'telemetry-unavailable'
  if s['disk_free_bytes']<r['safety_floor_free_disk_gib']*2**30:return 'disk-pressure'
  memory=max(s['ram_used_percent'],s.get('gpu_memory_percent',0));load=max(s['cpu_percent'],memory)
  if s.get('gpu_utilization_percent',0)>=78:
   if self.gpu_high_since is None:self.gpu_high_since=now
  else:self.gpu_high_since=None
  sustained=self.gpu_high_since is not None and now-self.gpu_high_since>=10
  if memory>=78:return 'shed'
  if load>=72 or sustained:self.paused=True;self.recovery=None
  if self.paused:
   if load<60 and s.get('gpu_utilization_percent',0)<60:
    if self.recovery is None:self.recovery=now
    if now-self.recovery>=15:self.paused=False;self.recovery=None
   else:self.recovery=None
  return 'pause' if self.paused else 'admit'

def fresh_host():
 try:
  s=json.loads((STATE/'host-telemetry.json').read_text())
  if time.time()-s['time']>5:raise ValueError()
  return s
 except Exception:raise RuntimeError('Fresh host telemetry unavailable; start the supervised host worker.')

def run(command,require_gpu=False,host=False,service=False):
 if service and (len(command)<2 or Path(command[1]).resolve()!=ROOT/'app.py' or Path(command[0]).absolute()!=ROOT/'.venv/bin/python'):raise RuntimeError('Service mode permits only the foreground FloorHAWK app launcher')
 deadline=json.loads((STATE/'preflight.json').read_text()).get('implementation_deadline_unix',float('inf')) if (STATE/'preflight.json').exists() else float('inf')
 if not service and time.time()>deadline:raise RuntimeError('Unattended build window expired; checkpoint retained. Manual foreground demo launch is separate.')
 if not service and any(module in command for module in ('v2.benchmark','v3.benchmark')) and time.time()>deadline-1800:raise RuntimeError('Benchmark admission closed for final verification reserve')
 env=os.environ.copy();env.update(YOLO_OFFLINE='true',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',WANDB_MODE='disabled',MPLCONFIGDIR=str(CACHE_ROOT/'matplotlib'),YOLO_CONFIG_DIR=str(CACHE_ROOT/'ultralytics'),ULTRALYTICS_AUTOINSTALL='false',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 a=Admission();s=sample(gpu=require_gpu) if not host else fresh_host();decision=a.check(s,require_gpu)
 if decision!='admit':raise RuntimeError('Admission denied: '+decision)
 p=subprocess.Popen(command,env=env,start_new_session=True);stopped=False;started=time.time()
 job_id=uuid.uuid4().hex;log=STATE/('resources-'+str(p.pid)+'-'+job_id+'.jsonl')
 try:
  with log.open('a') as f:
   while p.poll() is None:
    s=sample(p.pid,gpu=require_gpu) if not host else dict(fresh_host(),owned=sample(p.pid,gpu=False));decision=a.check(s,require_gpu);s['decision']=decision;s['job_id']=job_id;s['command_kind']=Path(command[0]).name+':'+str(command[2] if len(command)>2 and command[1]=='-m' else Path(command[1]).name if len(command)>1 else '');f.write(json.dumps(s)+'\n');f.flush()
    if (not service and (time.time()-started>POLICY['runtime_seconds_max'] or time.time()>deadline)) or decision in ('shed','telemetry-unavailable','disk-pressure'):
     os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=10)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
     raise RuntimeError('Owned workload checkpoint/stop: '+decision)
    if decision=='pause' and not stopped:os.killpg(p.pid,signal.SIGSTOP);stopped=True
    elif decision=='admit' and stopped:os.killpg(p.pid,signal.SIGCONT);stopped=False
    time.sleep(1)
  return p.returncode
 finally:
  if p.poll() is None:
   os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)

def main():
 p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');p.add_argument('--host',action='store_true');p.add_argument('--service',action='store_true',help='Manual foreground app only; budget/resource controls remain, autonomous build deadline is separate');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command
 if cmd and cmd[0]=='--':cmd=cmd[1:]
 if not cmd:p.error('command required')
 try:sys.exit(run(cmd,a.gpu,a.host,a.service))
 except RuntimeError as e:print(str(e),file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
