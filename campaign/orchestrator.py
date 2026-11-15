"""Phase/target enforcement. Only verified candidate manifests can trigger early freeze."""
import time,json,os,signal,shutil
from pathlib import Path
from .clock import DEADLINES,now,atomic,effective_target
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def freeze(best,reason):
 dest=OUT/'FROZEN.json'
 if dest.exists():return
 deployed=None
 try:deployed=json.loads((OUT/'DEPLOYMENT_CANDIDATE.json').read_text())
 except FileNotFoundError:pass
 atomic(dest,{'time':now(),'reason':reason,'best_verified':best,'deployment_candidate':deployed,'note':'Optimization admission closed; do not change frozen source/settings or grade based on final results. Best offline grouped estimate and verified production candidate can differ; preserve both explicitly.'})
def main():
 first85=None;last_phase=None
 while time.time()<=DEADLINES['evaluate']:
  current=time.time();best=None
  try:best=json.loads((OUT/'best-verified.json').read_text())
  except FileNotFoundError:pass
  if best and best.get('full_development_verified')and best.get('primary_accuracy',0)>=.85:
   if first85 is None:first85=current;atomic(OUT/'first-85.json',{'time':now(),'epoch':current,'new_target':effective_target(first85)})
   if best['primary_accuracy']>=effective_target(first85):freeze(best,'Verified early accuracy target reached')
  if current>=DEADLINES['optimize']:freeze(best,'05:45 Helsinki hard optimization deadline')
  phase='evaluate'if current>=DEADLINES['deploy']else'deploy'if(OUT/'FROZEN.json').exists()else'optimize'
  atomic(OUT/'orchestrator.json',{'pid':os.getpid(),'time':now(),'phase':phase,'deadlines':DEADLINES,'target':effective_target(first85),'first85_epoch':first85,'warm_event_deployments_excluded':True})
  for f in (OUT/'tasks').glob('*.json'):
   try:
    task=json.loads(f.read_text())
    if task.get('status')!='running':continue
    limit=min(task['deadline'],DEADLINES[task['phase']]);early=(OUT/'FROZEN.json').exists()and task['phase']=='optimize'
    if current>=limit or early:
     pgid=task['pgid']
     if pgid<=1 or pgid==os.getpgrp():continue
     os.killpg(pgid,signal.SIGCONT);os.killpg(pgid,signal.SIGTERM);task.update(status='orchestrator-stopped',finished=now(),reason='phase-deadline-or-verified-target');atomic(f,task)
   except(ProcessLookupError,FileNotFoundError,KeyError):pass
  time.sleep(5)
 atomic(OUT/'orchestrator.json',{'time':now(),'phase':'complete','status':'campaign stopped; intended event deployments excluded'})
if __name__=='__main__':main()
