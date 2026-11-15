import unittest,threading,copy,tempfile
from pathlib import Path
from deploy.modal.security import Controls,Denied
class Store:
 def __init__(self):self.rows={'admission-state-v1':{'events':[],'jobs':{},'idempotency':{},'live':True,'gemini':False}};self.lock=threading.Lock()
 def put(self,k,v,skip_if_exists=False):
  with self.lock:
   if skip_if_exists and k in self.rows:return False
   self.rows[k]=copy.deepcopy(v);return True
 def get(self,k,default=None):
  with self.lock:return copy.deepcopy(self.rows.get(k,default))
 def pop(self,k,default=None):
  with self.lock:return self.rows.pop(k,default)
class ModalTests(unittest.TestCase):
 def test_idempotent_recovery_never_charges_exhausted_budget_again(self):
  store=Store();controls=Controls(store,'');ident,_=controls.reserve('owner','same',False,'release','local');state=store.get('admission-state-v1');state['compute_reservation_usd']=7;state['live']=False;store.put('admission-state-v1',state);self.assertEqual(controls.reserve('owner','same',False,'release','local'),(ident,False));self.assertEqual(store.get('admission-state-v1')['compute_reservation_usd'],7)
  with self.assertRaises(Denied):controls.reserve('other','new',False,'release','local')
 def test_atomic_lock_and_fail_closed(self):
  s=Store();c=Controls(s,'');s.put('admission-lock-v1','crashed-owner')
  with self.assertRaises(Denied):c.reserve('s','i',False,'r','local')
  self.assertFalse(s.rows['admission-state-v1']['events'])
 def test_quota_idempotency_ownership_and_rollback(self):
  c=Controls(Store(),'');ident,new=c.reserve('s','i',True,'r','local');self.assertTrue(new);self.assertEqual(c.reserve('s','i',True,'r','local'),(ident,False))
  with self.assertRaises(Denied):c.reserve('s','i2',True,'r','local')
  with self.assertRaises(Denied):c.own('other',ident)
  c.rollback(ident);self.assertEqual(c.allowance()['questions_remaining'],5)
  for i in range(2):
   j,_=c.reserve('s'+str(i),str(i),True,'r','local');c.complete(j,'success')
  with self.assertRaises(Denied):c.reserve('s3','third',True,'r','local')
  self.assertEqual(c.allowance()['uploads_remaining'],0)
 def test_question_queue_and_compute_bounds(self):
  c=Controls(Store(),'')
  for i in range(5):
   j,_=c.reserve(str(i),str(i),False,'r','local');c.complete(j,'success')
  with self.assertRaises(Denied):c.reserve('six','six',False,'r','local')
 def test_missing_state_disables_admission(self):
  store=Store();store.rows.clear()
  with self.assertRaises(Denied):Controls(store,'').reserve('s','i',False,'r','local')
 def test_repeated_source_counts_once(self):
  c=Controls(Store(),'')
  for i in range(3):
   ident,_=c.reserve('same-session',str(i),'same-file-sha','r','local');c.complete(ident,'success')
  self.assertEqual(c.allowance()['uploads_remaining'],1)
 def test_gemini_disabled_and_gold_not_exported(self):
  with self.assertRaises(Denied):Controls(Store(),'').reserve('s','i',False,'r','hybrid')
  from deploy.modal.export_release import export
  import subprocess
  with tempfile.TemporaryDirectory()as d:
   out=Path(d)/'release';m=export('HEAD',out);self.assertFalse((out/'benchmarks').exists());self.assertFalse((out/'results').exists());self.assertTrue((out/'web/app.js').is_file());self.assertTrue((out/'deploy/modal/licenses/LICENSE.CubiCasa').is_file())
   b=Path(d)/'backend';n=export('HEAD',b,'backend',out);self.assertEqual(m['frontend_sha256'],n['frontend_sha256'])
