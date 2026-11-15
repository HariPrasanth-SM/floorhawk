"""Presenter dollar authority. No request-count or tiny-permit cap."""
import time,uuid,contextlib,math
import modal
from deploy.modal.cloud_budget import CloudLedger
from v2.budget import BudgetBlocked
class PresenterLedger(CloudLedger):
 def __init__(self):self.store=modal.Dict.from_name('floorhawk-presenter-budget-v1');self.path=None
 def summary(self):
  g=self.store.get('ui-release-grant-v1',{});reserved=sum(r['reserved']for r in g.get('records',[]));return {'requests_reserved':len(g.get('records',[])),'requests_max':None,'estimated_usd_reserved':reserved,'estimated_usd_max':g.get('allocated_usd',0),'note':'Non-overlapping presenter envelope already reserved in preserved canonical ledger; no artificial query cap'}
 @contextlib.contextmanager
 def reserve(self,operation,cost,concurrency=1):
  with self.transaction()as g:
   if not g.get('enabled'):raise BudgetBlocked('Presenter provider stop switch is off')
   if not isinstance(cost,(int,float))or isinstance(cost,bool)or not math.isfinite(cost)or cost<0:raise BudgetBlocked('Unknown finite request cost; no dispatch')
   if sum(r.get('status')=='reserved'for r in g['records'])>=2:raise BudgetBlocked('Shared provider concurrency is busy; Local result retained')
   if sum(r['reserved']for r in g['records'])+cost>g['allocated_usd']:raise BudgetBlocked('Presenter monetary envelope exhausted')
   ident=uuid.uuid4().hex;g['records'].append({'id':ident,'time':time.time(),'operation':operation,'reserved':cost,'status':'reserved','metadata':{}})
  try:yield ident
  except BaseException:self.finish(ident,'failed-or-ambiguous',{});raise
