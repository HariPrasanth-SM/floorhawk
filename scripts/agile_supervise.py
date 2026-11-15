"""Current user-authorized hour; unchanged lifetime ledger and monitored controls."""
import sys,os,time,json,subprocess,signal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT
from runtime_paths import RESULTS_ROOT,CACHE_ROOT
from v2.supervisor import sample,fresh_host,Admission
O=RESULTS_ROOT/'agile1';a=json.loads((O/'authorization.json').read_text());stop=a['experiment_stop_epoch'];p=None;paused=False;admit=Admission()
def terminate(signum,frame):
 raise SystemExit('Owned supervisor interrupted')
signal.signal(signal.SIGTERM,terminate)
try:
 if time.time()>stop:raise RuntimeError('Current hour experiment window closed')
 if admit.check(fresh_host())!='admit':raise RuntimeError('Resource admission denied')
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',YOLO_OFFLINE='true',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLCONFIGDIR=str(CACHE_ROOT/'matplotlib'),YOLO_CONFIG_DIR=str(CACHE_ROOT/'ultralytics'));p=subprocess.Popen([sys.executable,'scripts/agile_run.py'],cwd=ROOT,env=env,start_new_session=True)
 with(O/'resource-telemetry.jsonl').open('a')as f:
  while p.poll()is None:
   s=sample(p.pid,gpu=False);host=fresh_host();s.update({k:v for k,v in host.items()if k.startswith('gpu_')});d=admit.check(s);f.write(json.dumps(dict(s,decision=d))+'\n');f.flush()
   if time.time()>stop or d in['shed','disk-pressure','telemetry-unavailable']:raise RuntimeError('Owned experiment stopped by deadline/resource policy')
   if d=='pause'and not paused:os.killpg(p.pid,signal.SIGSTOP);paused=True
   elif d=='admit'and paused:os.killpg(p.pid,signal.SIGCONT);paused=False
   time.sleep(1)
finally:
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
