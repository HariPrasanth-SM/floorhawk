"""Private operator commands. Never prints access-code/session secret values."""
import argparse,json,subprocess,sys
from pathlib import Path
import modal
p=argparse.ArgumentParser();p.add_argument('action',choices=['status','disable','enable','recover-lock']);p.add_argument('--role',choices=['public','presenter','judges','candidate'],default='public');p.add_argument('--verified-report',type=Path);p.add_argument('--confirm-app-stopped',action='store_true');a=p.parse_args();roles={'public':('floorhawk-demo','floorhawk-control-v1'),'presenter':('floorhawk-presenter','floorhawk-presenter-control-v1'),'judges':('floorhawk-judges','floorhawk-judges-control-v1'),'candidate':('floorhawk-overnight-candidate','floorhawk-candidate-control-v1')};app_name,control_name=roles[a.role];s=modal.Dict.from_name(control_name);lock='admission-lock-v1'
if a.action=='recover-lock':
 if not a.confirm_app_stopped:raise SystemExit('Stop '+app_name+' first, then --confirm-app-stopped. Never unlock a live owner.')
 rows=json.loads(subprocess.check_output([str(Path(sys.executable).parent/'modal'),'app','list','--json'],text=True))
 active=[r for r in rows if (r.get('description')or r.get('Description')or r.get('Name')or r.get('name'))==app_name and str(r.get('State',r.get('state',''))).lower()not in ['stopped','disabled']]
 if active:raise SystemExit('App still present/active: refusing lock recovery')
 s.pop(lock,None)
 x=s.get('admission-state-v1',{})
 for row in x.get('jobs',{}).values():
  if row['status']in ['reserved','queued','running']:row.update(status='execution_error',recovery_reason='Operator verified app stopped; orphaned work interrupted')
 x.update(live=False,gemini=False,verification_sessions=[]);s.put('admission-state-v1',x)
 print('Stopped-app admission lock recovered; live remains disabled');a.action='disable'
if a.action=='status':
 x=s.get('admission-state-v1',{});print(json.dumps({'role':a.role,'live':x.get('live',False),'gemini':x.get('gemini',False),'lock_present':s.contains(lock),'active_jobs':sum(j['status']in ['reserved','queued','running']for j in x.get('jobs',{}).values()),'compute_reservation_usd':x.get('compute_reservation_usd',0)},indent=2));raise SystemExit
if a.action=='enable':
 if not a.verified_report:raise SystemExit('Require --verified-report with completed protected cloud smoke checks')
 report=json.loads(a.verified_report.read_text())
 if not report.get('passed'):raise SystemExit('Cloud verification report did not pass')
if not s.put(lock,'operator',skip_if_exists=True):raise SystemExit('Admission locked: fail closed; inspect owner')
try:
 x=s.get('admission-state-v1',{'events':[],'jobs':{},'idempotency':{}});hybrid=bool(a.action=='enable'and report.get('jobs')and all(j.get('status')=='success'and j.get('attempts',0)>=1 for j in report['jobs']))if a.action=='enable'else False
 x.update(live=a.action=='enable',gemini=hybrid,verification_sessions=[])
 s.put('admission-state-v1',x)
finally:s.pop(lock,None)
print('Live',a.action=='enable','Gemini',x.get('gemini',False))
