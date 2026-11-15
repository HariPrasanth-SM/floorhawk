"""Run a checkpointing owned process group with hard deadlines/resource supervision."""
import argparse,subprocess,os,time,signal,json,psutil,shutil
from pathlib import Path
from .clock import DEADLINES,admit,now,atomic
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'results/overnight-20261115'
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=DEADLINES,required=True);p.add_argument('--seconds',type=int,required=True);p.add_argument('--label',required=True);p.add_argument('cmd',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.cmd[1:]if a.cmd and a.cmd[0]=='--'else a.cmd;admit(a.phase,30);end=min(time.time()+a.seconds,DEADLINES[a.phase]);log=STATE/(a.label+'.log');meta=STATE/'tasks'/(a.label+'.json')
 with log.open('a')as f:
  child=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'));record={'label':a.label,'pid':child.pid,'pgid':0,'supervisor_owned_pgid':child.pid,'note':'Parent enforces child process-group deadline within its own PID namespace; global coordinator must not signal namespace-local PID','phase':a.phase,'deadline':end,'started':now(),'status':'running','command':cmd};atomic(meta,record);paused=False;reason=None;good=None
  try:
   while child.poll()is None:
    mem=psutil.virtual_memory().percent;disk=shutil.disk_usage(ROOT).free/1024**3
    if time.time()>=end or disk<15 or mem>=78 or(a.phase=='optimize'and(STATE/'FROZEN.json').exists()):reason='deadline'if time.time()>=end else'disk-reserve'if disk<15 else'RAM-pressure';break
    if mem>=72 and not paused:os.killpg(child.pid,signal.SIGSTOP);paused=True;good=None
    elif paused and mem<60:
     good=good or time.time()
     if time.time()-good>=15:os.killpg(child.pid,signal.SIGCONT);paused=False
    elif mem>=60:good=None
    time.sleep(1)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGCONT);os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=8)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   record.update(status='complete'if child.returncode==0 else'stopped',reason=reason,returncode=child.returncode,finished=now());atomic(meta,record)
 print(json.dumps(record));raise SystemExit(child.returncode)
if __name__=='__main__':main()
