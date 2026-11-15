"""Current25-minute task authorization only; preserves original Admission thresholds."""
import sys,os,time,signal,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT
from runtime_paths import RESULTS_ROOT,CACHE_ROOT
from v2.supervisor import Admission,sample,fresh_host
from datetime import datetime
stop=datetime.fromisoformat('2026-11-14T15:25:30+00:00').timestamp();admit=Admission();p=None;paused=False
try:
 if time.time()>stop:raise RuntimeError('Feature/experiment window closed')
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLCONFIGDIR=str(CACHE_ROOT/'matplotlib'),YOLO_CONFIG_DIR=str(CACHE_ROOT/'ultralytics'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',YOLO_OFFLINE='true');p=subprocess.Popen([sys.executable,'scripts/samples_smoke.py'],cwd=ROOT,env=env,start_new_session=True)
 with(RESULTS_ROOT/'samples25/resources.jsonl').open('a')as f:
  while p.poll()is None:
   telemetry=fresh_host();s=sample(p.pid,gpu=False);s.update({k:v for k,v in telemetry.items()if k.startswith('gpu_')});d=admit.check(s);f.write(json.dumps(dict(s,decision=d))+'\n');f.flush()
   if time.time()>stop or d in['shed','disk-pressure','telemetry-unavailable']:raise RuntimeError('Bounded experiment stopped')
   if d=='pause'and not paused:os.killpg(p.pid,signal.SIGSTOP);paused=True
   elif d=='admit'and paused:os.killpg(p.pid,signal.SIGCONT);paused=False
   time.sleep(1)
finally:
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
