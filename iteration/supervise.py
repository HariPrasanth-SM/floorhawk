"""Current explicitly approved60-minute window; original admission controls retained."""
import os,sys,time,json,subprocess,signal
from qa.common import write_json
from runtime_paths import RESULTS_ROOT,CACHE_ROOT
from v2.supervisor import Admission,sample,fresh_host
O=RESULTS_ROOT/'iteration60'
def main():
 a=json.loads((O/'authorization.json').read_text());cmd=sys.argv[1:];cmd=cmd[1:]if cmd and cmd[0]=='--'else cmd
 if not cmd or time.time()>a['feature_stop_epoch']:raise RuntimeError('Candidate work window closed')
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',YOLO_OFFLINE='true',ULTRALYTICS_AUTOINSTALL='false',MPLCONFIGDIR=str(CACHE_ROOT/'matplotlib'),YOLO_CONFIG_DIR=str(CACHE_ROOT/'ultralytics'),DO_NOT_TRACK='1');p=None;admission=Admission();paused=False
 def telemetry(pid=None):
  own=sample(pid,gpu=False)
  try:host=fresh_host();own.update({k:v for k,v in host.items()if k.startswith('gpu_')})
  except RuntimeError:pass
  return own
 if admission.check(telemetry())!='admit':raise RuntimeError('Resource admission unavailable')
 try:
  p=subprocess.Popen(cmd,env=env,start_new_session=True)
  with(O/'resource-telemetry.jsonl').open('a')as f:
   while p.poll()is None:
    s=telemetry(p.pid);d=admission.check(s);f.write(json.dumps(dict(s,decision=d))+'\n');f.flush()
    if time.time()>a['feature_stop_epoch']or d in['shed','disk-pressure','telemetry-unavailable']:raise RuntimeError('Deadline/resource stop; saved partials retained')
    if d=='pause'and not paused:os.killpg(p.pid,signal.SIGSTOP);paused=True
    elif d=='admit'and paused:os.killpg(p.pid,signal.SIGCONT);paused=False
    time.sleep(1)
  return p.returncode
 finally:
  if p and p.poll()is None:
   os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':sys.exit(main())
