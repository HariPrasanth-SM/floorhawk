"""SQLite atomic global reservation. Ambiguous/failed costs remain spent.
The single flight lock is held through the HTTP operation; no automatic retries.
"""
import contextlib,fcntl,json,sqlite3,time,uuid
from pathlib import Path
from .policy import STATE,POLICY
from runtime_paths import BUDGET_LEDGER
class BudgetBlocked(RuntimeError):pass
class Ledger:
 def __init__(self,path=None,requests=None,dollars=None):
  self.path=Path(path or BUDGET_LEDGER);
  if path is None and not self.path.is_file():raise BudgetBlocked('Restore the existing shared lifetime ledger; empty default ledgers are not created automatically')
  self.path.parent.mkdir(parents=True,exist_ok=True);self.max_requests=requests if requests is not None else POLICY['gemini']['api_requests_max'];self.max_cost=dollars if dollars is not None else POLICY['gemini']['estimated_cost_usd_max']
  with self.connect() as c:c.execute('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, time REAL, operation TEXT, reserved REAL, status TEXT, metadata TEXT)')
 def connect(self):return sqlite3.connect(self.path,timeout=10)
 def summary(self):
  with self.connect() as c:
   n,cost=c.execute('SELECT COUNT(*),COALESCE(SUM(reserved),0) FROM attempts').fetchone()
  return {'requests_reserved':n,'estimated_usd_reserved':cost,'requests_max':self.max_requests,'estimated_usd_max':self.max_cost}
 @contextlib.contextmanager
 def reserve(self,operation,cost,concurrency=1):
  if not 0<=cost<=self.max_cost:raise BudgetBlocked('Unknown or invalid conservative cost')
  if concurrency not in(1,2):raise BudgetBlocked('Cloud queue bound must be1 or2')
  selected=None
  for slot in range(concurrency):
   f=self.path.with_suffix('.flight.lock'if slot==0 else'.flight-1.lock').open('a')
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);selected=f;break
   except BlockingIOError:f.close()
  if selected is None:raise BudgetBlocked('Cloud operation already in flight')
  with selected as f:
   with self.connect() as c:
    c.execute('BEGIN IMMEDIATE');n,total=c.execute('SELECT COUNT(*),COALESCE(SUM(reserved),0) FROM attempts').fetchone();recent=c.execute('SELECT COUNT(*) FROM attempts WHERE time>?',(time.time()-60,)).fetchone()[0]
    if n>=self.max_requests or total+cost>self.max_cost:raise BudgetBlocked('Global Gemini allowance exhausted')
    if recent>=6:raise BudgetBlocked('Cloud rate limit: six requests per minute; retry later')
    ident=uuid.uuid4().hex;c.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?)',(ident,time.time(),operation,cost,'reserved','{}'))
   try:yield ident
   except BaseException:
    self.finish(ident,'failed-or-ambiguous',{});raise
 def finish(self,ident,status,metadata):
  allowed={k:v for k,v in metadata.items() if k in ('model','input_tokens','output_tokens','thinking_tokens','latency_seconds','http_status','prompt_version')}
  with self.connect() as c:c.execute('UPDATE attempts SET status=?,metadata=? WHERE id=?',(status,json.dumps(allowed),ident))
