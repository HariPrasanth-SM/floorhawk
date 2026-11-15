from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""New user-authorized audit window; retains original pressure controls and lock."""
import sys,json,time,subprocess,os,signal,uuid
from qa.common import ROOT
from v2.supervisor import Admission,fresh_host,sample

def main():
 a=json.loads((RESULTS_ROOT/'inspection/authorization.json').read_text());cmd=sys.argv[1:];cmd=cmd[1:] if cmd and cmd[0]=='--' else cmd
 if not cmd or time.time()>a['deadline']:raise RuntimeError('Inspection window closed')
 decision=Admission();s=sample(gpu=False)
 if decision.check(s)!='admit':raise RuntimeError('Resource admission denied')
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',YOLO_OFFLINE='true',HF_HUB_DISABLE_TELEMETRY='1',WANDB_MODE='disabled',MPLCONFIGDIR=str(CACHE_ROOT/'matplotlib'),YOLO_CONFIG_DIR=str(CACHE_ROOT/'ultralytics'),ULTRALYTICS_AUTOINSTALL='false',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false');p=subprocess.Popen(cmd,env=env,start_new_session=True);stopped=False
 try:
  with (RESULTS_ROOT/'inspection'/('resources-'+uuid.uuid4().hex+'.jsonl')).open('w') as f:
   while p.poll() is None:
    s=sample(p.pid,gpu=False);d=decision.check(s);s['decision']=d;f.write(json.dumps(s)+'\n');f.flush()
    if time.time()>a['deadline'] or d in ('shed','telemetry-unavailable','disk-pressure'):raise RuntimeError('Checkpoint and stop: '+d)
    if d=='pause' and not stopped:os.killpg(p.pid,signal.SIGSTOP);stopped=True
    elif d=='admit' and stopped:os.killpg(p.pid,signal.SIGCONT);stopped=False
    time.sleep(1)
  return p.returncode
 finally:
  if p.poll() is None:os.killpg(p.pid,signal.SIGCONT);os.killpg(p.pid,signal.SIGTERM)
if __name__=='__main__':sys.exit(main())
