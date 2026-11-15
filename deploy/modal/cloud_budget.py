"""Durable consumption of prepaid, non-overlapping canonical-ledger permits."""
import contextlib,json,time,sqlite3
import modal
from v2.budget import BudgetBlocked
STORE='floorhawk-gemini-budget-v1';KEY='ui-release-grant-v1'
class CloudLedger:
 def __init__(self):self.store=modal.Dict.from_name(STORE);self.path=None
 @contextlib.contextmanager
 def transaction(self):
  if not self.store.put('lock','budget-operation',skip_if_exists=True):raise BudgetBlocked('Cloud budget busy; retry later')
  try:
   grant=self.store.get(KEY)
   if not grant:raise BudgetBlocked('No prepaid cloud request permits')
   yield grant
   self.store.put(KEY,grant)
  finally:self.store.pop('lock',None)
 def summary(self):
  g=self.store.get(KEY,{})
  return dict(g.get('canonical_summary',{}),cloud_attempts=len(g.get('records',[])),cloud_permits_remaining=len(g.get('permits',[]))-len(g.get('records',[])),budget_note='Cloud permits are already reserved in canonical lifetime ledger; not independent spending')
 @contextlib.contextmanager
 def reserve(self,operation,cost,concurrency=1):
  with self.transaction()as g:
   rows=g['records'];used={r['id']for r in rows};available=[p for p in g['permits']if p['id']not in used]
   if not available or len(rows)>=30:raise BudgetBlocked('This iteration cloud allowance exhausted (30 attempts maximum)')
   if sum(r['time']>time.time()-60 for r in rows)>=6:raise BudgetBlocked('Cloud rate limit: six attempts/minute')
   permit=available[0]
   if cost>permit['reserved']:raise BudgetBlocked('Request exceeds prepaid conservative reservation')
   ident=permit['id'];rows.append({'id':ident,'time':time.time(),'operation':operation,'reserved':permit['reserved'],'requested_reservation':cost,'status':'reserved','metadata':{}})
  try:yield ident
  except BaseException:self.finish(ident,'failed-or-ambiguous',{});raise
 def finish(self,ident,status,metadata):
  with self.transaction()as g:
   for r in g['records']:
    if r['id']==ident:r.update(status=status,metadata={k:v for k,v in metadata.items()if k in ['model','http_status','latency_seconds','prompt_version','input_tokens','output_tokens','thinking_tokens']})
 @contextlib.contextmanager
 def connect(self):
  # Read-only SQL-shaped projection for the existing adapter; never a spending authority.
  g=self.store.get(KEY,{});c=sqlite3.connect(':memory:');c.execute('CREATE TABLE attempts(id,time,operation,reserved,status,metadata)')
  c.executemany('INSERT INTO attempts VALUES(?,?,?,?,?,?)',[(r['id'],r['time'],r['operation'],r['reserved'],r['status'],json.dumps(r['metadata']))for r in g.get('records',[])])
  try:yield c
  finally:c.close()
