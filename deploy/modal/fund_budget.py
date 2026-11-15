"""Idempotent prepaid sub-budget. Original rows/history are never reset/refunded."""
import sys,json,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
if '--public-event-limit' in sys.argv:
 from event_allocation import main
 main()
 raise SystemExit
from v2.budget import Ledger
import modal
operation='modal-ui-release-20261114-prefund';ledger=Ledger()
with ledger.connect()as c:
 c.execute('BEGIN IMMEDIATE');rows=c.execute('SELECT id,reserved FROM attempts WHERE operation=?',(operation,)).fetchall()
 if not rows:
  n,total=c.execute('SELECT COUNT(*),COALESCE(SUM(reserved),0)FROM attempts').fetchone()
  if n+30>ledger.max_requests or total+.6>100:raise SystemExit('Existing lifetime allowance insufficient')
  rows=[(uuid.uuid4().hex,.02)for _ in range(30)]
  c.executemany('INSERT INTO attempts VALUES(?,?,?,?,?,?)',[(i,time.time(),operation,cost,'prepaid-cloud-permit','{}')for i,cost in rows])
 if len(rows)!=30:raise SystemExit('Unexpected previous allocation; inspect, do not overwrite')
summary=ledger.summary();g={'permits':[{'id':i,'reserved':cost}for i,cost in rows],'records':[],'canonical_summary':summary,'allocation_note':'30 attempts / $0.60 prepaid and included in canonical $100/1000 cap; unspent permits are NOT HTTP calls'}
s=modal.Dict.from_name('floorhawk-gemini-budget-v1',create_if_missing=True)
if not s.put('ui-release-grant-v1',g,skip_if_exists=True):
 old=s.get('ui-release-grant-v1');assert {p['id']for p in old['permits']}=={i for i,_ in rows}
Path('deploy/modal/budget-snapshot.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'canonical_summary':summary,'cloud_prepaid_permits':30,'cloud_prepaid_usd':.6}))
