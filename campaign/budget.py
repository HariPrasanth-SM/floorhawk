"""Same durable presenter monetary authority; bounded contention wait, no new grant."""
import contextlib,time,uuid
from deploy.modal.presenter_budget import PresenterLedger
from v2.budget import BudgetBlocked
class CampaignLedger(PresenterLedger):
 @contextlib.contextmanager
 def transaction(self):
  owner='campaign-'+uuid.uuid4().hex;end=time.monotonic()+5
  while not self.store.put('lock',owner,skip_if_exists=True):
   if time.monotonic()>end:raise BudgetBlocked('Shared monetary authority busy; no dispatch')
   time.sleep(.08)
  try:
   g=self.store.get('ui-release-grant-v1')
   if not g:raise BudgetBlocked('Existing monetary envelope unavailable')
   yield g;self.store.put('ui-release-grant-v1',g)
  finally:
   if self.store.get('lock')==owner:self.store.pop('lock',None)
 @contextlib.contextmanager
 def reserve(self,operation,cost,concurrency=1):
  import math
  with self.transaction()as g:
   if not g.get('enabled'):raise BudgetBlocked('Existing monetary stop switch is off')
   if not isinstance(cost,(int,float))or not math.isfinite(cost)or cost<0:raise BudgetBlocked('Unknown request cost')
   remaining=g['allocated_usd']-sum(r['reserved']for r in g['records'])
   if remaining-cost<10:raise BudgetBlocked('Campaign stopped to preserve event serving reserve')
   ident=uuid.uuid4().hex;g['records'].append({'id':ident,'time':time.time(),'operation':operation,'reserved':cost,'status':'reserved','metadata':{}})
  try:yield ident
  except BaseException:self.finish(ident,'failed-or-ambiguous',{});raise
