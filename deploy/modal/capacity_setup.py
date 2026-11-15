"""Record explicitly authorized event cap retirement without deleting history."""
import json,time
from pathlib import Path
import modal
from deploy.modal.security import Controls
from deploy.modal.presenter_budget import PresenterLedger
from deploy.modal.event_policy import policy

def main():
 cfg=policy();stamp=time.time()
 for name in ['floorhawk-presenter-control-v1','floorhawk-judges-control-v1','floorhawk-control-v1']:
  store=modal.Dict.from_name(name)
  with Controls(store,'').transaction()as s:
   if s.get('event_capacity_policy')!=cfg['version']:s.setdefault('capacity_policy_history',[]).append({'time':stamp,'version':cfg['version'],'previous_compute_limit':s.get('compute_limit_usd'),'retained_historical_reservations':s.get('compute_reservation_usd',0),'note':cfg['authorization']})
   s['event_capacity_policy']=cfg['version'];s['application_caps_disabled']=True
 ledger=PresenterLedger()
 with ledger.transaction()as g:
  if not g.get('event_caps_disabled'):g.setdefault('policy_history',[]).append({'time':stamp,'action':'Retire event dollar/permit/cumulative query gates; existing records and allocations retained as historical accounting','authorization':cfg['authorization']})
  g['event_caps_disabled']=True
 print(json.dumps({'policy':cfg,'shared_accounting_records':ledger.summary()['requests_reserved'],'histories_preserved':True,'note':'New runtime uses explicit event policy; no provider quota or billing setting changed'}))
if __name__=='__main__':main()
