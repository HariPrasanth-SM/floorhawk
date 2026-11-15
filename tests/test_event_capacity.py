import os,unittest
from unittest.mock import patch
from tests.test_modal_deploy import Store
from deploy.modal.security import Controls,Denied
from deploy.modal.presenter_budget import PresenterLedger
class EventCapacityTests(unittest.TestCase):
 def test_retired_caps_preserve_history_and_session_bounds(self):
  s=Store();x=s.get('admission-state-v1');x.update(compute_limit_usd=0,compute_reservation_usd=999);s.put('admission-state-v1',x)
  with patch.dict(os.environ,{'FLOORHAWK_EVENT_CAPACITY':'1','FLOORHAWK_EVENT_ROLE':'public'}):
   c=Controls(s,'')
   for i in range(40):
    j,_=c.reserve('visitor'+str(i),str(i),True,'release','local');c.complete(j,'success')
   self.assertEqual(s.get('admission-state-v1')['compute_reservation_usd'],999);self.assertIsNone(c.allowance()['questions_remaining'])
   j,_=c.reserve('v','same',True,'r','local');self.assertEqual(c.reserve('v','same',True,'r','local'),(j,False))
   with self.assertRaises(Denied):c.reserve('v','new',False,'r','local')
 def test_burst_and_queue_still_bound(self):
  with patch.dict(os.environ,{'FLOORHAWK_EVENT_CAPACITY':'1','FLOORHAWK_EVENT_ROLE':'public'}):
   c=Controls(Store(),'')
   for i in range(6):j,_=c.reserve('bot',str(i),False,'r','local');c.complete(j,'success')
   with self.assertRaises(Denied):c.reserve('bot','flood',False,'r','local')
   c=Controls(Store(),'')
   for i in range(25):c.reserve(str(i),str(i),False,'r','local')
   with self.assertRaises(Denied):c.reserve('26','26',False,'r','local')
 def test_provider_accounting_has_no_event_money_gate(self):
  s=Store();s.rows['ui-release-grant-v1']={'allocated_usd':0,'enabled':True,'records':[]}
  with patch.dict(os.environ,{'FLOORHAWK_EVENT_CAPACITY':'1'}),patch('modal.Dict.from_name',return_value=s):
   c=PresenterLedger()
   with c.reserve('test',100):pass
   self.assertFalse(c.summary()['application_cap_enforced']);self.assertEqual(c.summary()['estimated_usd_reserved'],100)
   s.rows['ui-release-grant-v1']['enabled']=False
   with self.assertRaises(Exception):
    with c.reserve('stopped',.1):pass
