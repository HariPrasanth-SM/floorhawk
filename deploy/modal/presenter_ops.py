"""Operate isolated event roles; default remains the existing presenter."""
import argparse,json,subprocess,sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import modal
EVENT_APPS=['floorhawk-presenter','floorhawk-judges','floorhawk-demo','floorhawk-overnight-candidate']
APPS=EVENT_APPS+['floorhawk-campaign-extraction','floorhawk-final-evaluation']
p=argparse.ArgumentParser();p.add_argument('action',choices=['warm','ready','status','off','stop']);p.add_argument('--app',choices=APPS,default='floorhawk-presenter');p.add_argument('--budget',action='store_true');p.add_argument('--admission',action='store_true');a=p.parse_args()
if a.action=='stop':raise SystemExit(subprocess.run([str(Path(sys.executable).parent/'modal'),'app','stop',a.app,'--yes']).returncode)
if a.app not in EVENT_APPS and a.action!='status':raise SystemExit('Campaign apps support read-only status or explicit stop; no accidental warming')
kind={'floorhawk-campaign-extraction':('Extractor','extract'),'floorhawk-final-evaluation':('FinalWorker','evaluate')}.get(a.app,('Resident','ready'));m=modal.Cls.from_name(a.app,kind[0])()
if a.action=='status':
 try:print(getattr(m,kind[1]).get_current_stats())
 except Exception as e:print('Resident stats unavailable:',type(e).__name__,'(legacy or stopped deployment)')
 if a.admission and a.app in EVENT_APPS:
  name={'floorhawk-presenter':'floorhawk-presenter-control-v1','floorhawk-judges':'floorhawk-judges-control-v1','floorhawk-demo':'floorhawk-control-v1','floorhawk-overnight-candidate':'floorhawk-candidate-control-v1'}[a.app];store=modal.Dict.from_name(name);state=store.get('admission-state-v1',{});print(json.dumps({'app':a.app,'live':state.get('live',False),'gemini':state.get('gemini',False),'lock_present':store.contains('admission-lock-v1'),'active_jobs':sum(j['status']in ['reserved','queued','running']for j in state.get('jobs',{}).values()),'compute_reservation_usd':state.get('compute_reservation_usd',0),'durable_job_statuses':dict(collections.Counter(j['status']for j in state.get('jobs',{}).values()))},indent=2))
 if a.budget:
  from deploy.modal.presenter_budget import PresenterLedger
  from v2.gemini import MODEL_PRICES
  ledger=PresenterLedger();g=ledger.store.get('ui-release-grant-v1');rows=g.get('records',[]);by=collections.defaultdict(lambda:{'http_reservations':0,'reserved_usd':0,'known_input_tokens':0,'known_output_tokens':0,'known_thinking_tokens':0,'unknown_thinking_records':0,'known_token_estimate_usd':0.})
  for r in rows:
   meta=r.get('metadata',{});model=meta.get('model','unknown');s=by[model];s['http_reservations']+=1;s['reserved_usd']+=r['reserved'];s['known_input_tokens']+=meta.get('input_tokens')or 0;s['known_output_tokens']+=meta.get('output_tokens')or 0;s['known_thinking_tokens']+=meta.get('thinking_tokens')or 0;s['unknown_thinking_records']+='thinking_tokens'not in meta
   if model in MODEL_PRICES:
    pin,pout=MODEL_PRICES[model];s['known_token_estimate_usd']+=((meta.get('input_tokens')or 0)*pin+((meta.get('output_tokens')or 0)+(meta.get('thinking_tokens')or 0))*pout)/1e6
  print(json.dumps({'budget':ledger.summary(),'by_model':dict(by),'states':dict(collections.Counter(r['status']for r in rows)),'note':'Reservations are not actual billing; unknown thinking/tokens retained, no independent spending allowance'},indent=2))
  # Read-only lifetime reconciliation. Prepaid/envelope allocations are not HTTP
  # attempts, and the old cloud rows share IDs with canonical permits.
  import sqlite3
  from runtime_paths import BUDGET_LEDGER
  canonical=[]
  if BUDGET_LEDGER.is_file():
   with sqlite3.connect('file:'+str(BUDGET_LEDGER)+'?mode=ro',uri=True)as conn:
    canonical=[{'id':i,'reserved':cost,'status':status,'metadata':json.loads(meta)}for i,cost,status,meta in conn.execute('SELECT id,reserved,status,metadata FROM attempts')]
  try:old=modal.Dict.from_name('floorhawk-gemini-budget-v1').get('ui-release-grant-v1',{}).get('records',[])
  except Exception:old=[]
  combined={r['id']:r for r in canonical if r['status']not in ['allocated-presenter-envelope','prepaid-cloud-permit']};combined.update({r['id']:r for r in old});combined.update({r['id']:r for r in rows});known=0.;unknown_models=collections.Counter();unknown_usage=0
  for r in combined.values():
   meta=r.get('metadata',{});model=meta.get('model');price=MODEL_PRICES.get(model)
   if not price:unknown_models[model or 'unrecorded']+=1
   if 'input_tokens'not in meta or'output_tokens'not in meta:unknown_usage+=1
   if price:known+=((meta.get('input_tokens')or 0)*price[0]+((meta.get('output_tokens')or 0)+(meta.get('thinking_tokens')or 0))*price[1])/1e6
  print(json.dumps({'lifetime_reconciliation':{'canonical_entries':len(canonical),'canonical_reservations_including_existing_envelope_usd':sum(r['reserved']for r in canonical),'old_cloud_recorded_attempts':len(old),'shared_envelope_recorded_attempts':len(rows),'deduplicated_attempt_records':len(combined),'states':dict(collections.Counter(r['status']for r in combined.values())),'known_token_priced_subtotal_usd':known,'known_tokens':{k:sum((r.get('metadata',{}).get(k)or 0)for r in combined.values())for k in ['input_tokens','output_tokens','thinking_tokens']},'unknown_thinking_records':sum(not isinstance(r.get('metadata',{}).get('thinking_tokens'),int)for r in combined.values()),'missing_usage_records':unknown_usage,'unpriced_or_unknown_model_records':dict(unknown_models),'note':'Shared80USD allocation is already inside canonical reservations; NEVER add it again. Known token subtotal is partial, not actual provider billing; unresolved and unused reservations are retained.'}},indent=2))
 raise SystemExit
if a.action=='off':
 m.update_autoscaler(min_containers=0,max_containers=1,scaledown_window=2);print('Warming off for',a.app,'; queries may cold-start. Use stop to disable this deployment entirely.');raise SystemExit
if a.action=='warm':m.update_autoscaler(min_containers=1,max_containers=1,scaledown_window=120)
print(json.dumps(m.ready.remote(),indent=2))
