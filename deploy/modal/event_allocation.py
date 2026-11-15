"""Audited increase of public compute allocation; never resets reservations."""
import argparse,json,time,math
from pathlib import Path
import modal
from deploy.modal.security import Controls

def main():
 p=argparse.ArgumentParser();p.add_argument('--public-event-limit',type=float,required=True);a=p.parse_args()
 if not math.isfinite(a.public_event_limit)or not 7<=a.public_event_limit<=15:raise ValueError('This bounded event operation permits7–15USD total only')
 b=modal.Workspace.from_context().billing.summary(cycle='this month');billing={'metered_cost':str(b.metered_cost),'billed_cost':str(b.billed_cost),'adjustments':{k:str(v)for k,v in b.adjustments.items()},'limitation':'Remaining promotional credit is not exposed; billing can lag. Modest8USD increase maximum; no billing-plan change.'}
 store=modal.Dict.from_name('floorhawk-control-v1')
 with Controls(store,'').transaction()as s:
  before=s.get('compute_limit_usd',7);spent=s.get('compute_reservation_usd',0)
  if a.public_event_limit<before:raise ValueError('This operation never silently shrinks an allocation')
  if a.public_event_limit>before:s.setdefault('compute_allocation_history',[]).append({'time':time.time(),'previous_limit_usd':before,'new_limit_usd':a.public_event_limit,'reserved_at_change_usd':spent,'authorization':'User-authorized event-readiness allocation increase2026-11-15','billing_snapshot':billing})
  s['compute_limit_usd']=a.public_event_limit
 report={'billing':billing,'previous_limit_usd':before,'limit_usd':a.public_event_limit,'reserved_usd':spent,'estimated_query_capacity':max(0,int((a.public_event_limit-spent+1e-9)/.25)),'note':'Conservative application reservations, not actual invoiced spend. Existing events/jobs/idempotency/Gemini history preserved. Runtime operational update required.'};out=Path(__file__).resolve().parents[3]/'floorhawk-modal/verification/event-readiness';out.mkdir(parents=True,exist_ok=True);(out/'allocation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
