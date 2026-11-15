"""Stop only registered task-owned process groups at their wall-clock phase deadline."""
import os,sys,time,signal,json
from pathlib import Path
from .clock import DEADLINES,now,atomic
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'results/overnight-20261115';STATE.mkdir(exist_ok=True)
def main():
 atomic(STATE/'watchdog.json',{'pid':os.getpid(),'started':now(),'deadlines':DEADLINES,'status':'running'})
 while time.time()<DEADLINES['evaluate']:
  for p in (STATE/'tasks').glob('*.json')if(STATE/'tasks').exists()else[]:
   try:
    s=json.loads(p.read_text());deadline=min(float(s['deadline']),DEADLINES[s['phase']])
    if s.get('status')=='running'and time.time()>=deadline:
     pgid=int(s['pgid'])
     if pgid<=1 or pgid==os.getpgrp():continue
     os.killpg(pgid,signal.SIGTERM);s.update(status='deadline-stopped',stopped=now());atomic(p,s)
   except (ProcessLookupError,FileNotFoundError,ValueError):pass
  atomic(STATE/'heartbeat.json',{'time':now(),'optimize_remaining':max(0,DEADLINES['optimize']-time.time()),'final_remaining':max(0,DEADLINES['evaluate']-time.time())});time.sleep(10)
 atomic(STATE/'watchdog.json',{'pid':os.getpid(),'status':'complete','stopped':now(),'note':'Event deployments intentionally excluded; campaign workers enforce same deadlines'})
if __name__=='__main__':main()
