import unittest
from unittest.mock import patch
from tests.test_modal_deploy import Store
from deploy.modal.presenter_runtime import route_reason
class PresenterTests(unittest.TestCase):
 def test_router_general_not_identity_based(self):
  a={'status':'success','answer':2,'route':'ifc.structured','evidence':[{'id':'guid1'}]};self.assertIn('IFC',route_reason(a));self.assertEqual(route_reason(dict(a,source_sha256='anything')),route_reason(a))
  self.assertIsNone(route_reason(dict(a,status='abstained')))
 def test_counts_require_unique_instances(self):
  a={'status':'success','answer':2,'route':'raster.rtdetr-l.v3','task':{'target':'window'},'evidence':[{'id':'one'},{'id':'two'}]};self.assertTrue(route_reason(a));a['evidence'][1]['id']='one';self.assertIsNone(route_reason(a))
 def test_presenter_no_artificial_question_counter(self):
  from deploy.modal.presenter_controls import PresenterControls
  c=PresenterControls(Store(),'')
  for i in range(12):
   ident,_=c.reserve('presenter',str(i),True,'r','hybrid');c.complete(ident,'success')
  self.assertIsNone(c.allowance()['questions_remaining'])
 def test_dollar_budget_without_permit_cap(self):
  from deploy.modal.presenter_budget import PresenterLedger
  from v2.budget import BudgetBlocked
  s=Store();s.rows['ui-release-grant-v1']={'allocated_usd':80,'enabled':True,'records':[]}
  with patch('modal.Dict.from_name',return_value=s):
   c=PresenterLedger()
   for i in range(40):
    with c.reserve(str(i),.012)as ident:c.finish(ident,'http-response',{})
   self.assertEqual(c.summary()['requests_reserved'],40)
   for invalid in [float('nan'),float('inf'),-1,True,'unknown']:
    with self.assertRaises(BudgetBlocked):
     with c.reserve('invalid',invalid):pass
   with self.assertRaises(BudgetBlocked):
    with c.reserve('too-much',100):pass

 def test_completed_restore_uses_server_reference_and_restores_reuse(self):
  from pathlib import Path
  source=(Path(__file__).resolve().parents[1]/'web/app.js').read_text()
  self.assertIn('await restoreCompletedJob(job)',source)
  body=source.split('async function restoreCompletedJob(job){',1)[1]
  self.assertIn('showExpectedReference(job.expected_reference)',body)
  self.assertIn('S.reuseJobId=job.id;S.validated=true',body)
  self.assertIn("setPresenterTab(isCurated?'samples':'live')",body)

 def test_concurrent_monetary_reservations_never_exceed_authority(self):
  from deploy.modal.presenter_budget import PresenterLedger
  from v2.budget import BudgetBlocked
  from concurrent.futures import ThreadPoolExecutor
  store=Store();store.rows['ui-release-grant-v1']={'allocated_usd':80,'enabled':True,'records':[]}
  with patch('modal.Dict.from_name',return_value=store):
   ledger=PresenterLedger()
   def attempt(i):
    try:
     with ledger.reserve('concurrent-'+str(i),30):return True
    except BudgetBlocked:return False
   with ThreadPoolExecutor(max_workers=8)as pool:accepted=list(pool.map(attempt,range(20)))
   self.assertGreaterEqual(sum(accepted),1);self.assertLessEqual(sum(accepted),2);self.assertLessEqual(ledger.summary()['estimated_usd_reserved'],80)

 def test_gateway_has_no_conditional_hashlib_local(self):
  import ast
  from pathlib import Path
  source=ast.parse((Path(__file__).resolve().parents[1]/'deploy/modal/gateway.py').read_text())
  for node in ast.walk(source):
   if isinstance(node,ast.AsyncFunctionDef):
    self.assertFalse(any(isinstance(child,ast.Import)and any(a.name=='hashlib'for a in child.names)for child in ast.walk(node)), 'conditional import shadows global upload hashing')

 def test_slow_geometry_does_not_cancel_current_render(self):
  from pathlib import Path
  source=(Path(__file__).resolve().parents[1]/'web/app.js').read_text()
  timer=source.split("const previousModelContext=showModelContext;",1)[1].split('async function recoverSubmission',1)[0]
  self.assertNotIn('modelTicket++',timer)
  self.assertIn('loading IFC geometry in background',timer)
