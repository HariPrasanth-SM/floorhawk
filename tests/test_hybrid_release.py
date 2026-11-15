import unittest,copy,tempfile
from unittest.mock import patch
from tests.test_modal_deploy import Store
class BudgetTests(unittest.TestCase):
 def store(self):
  s=Store();s.rows['ui-release-grant-v1']={'permits':[{'id':str(i),'reserved':.02}for i in range(30)],'records':[],'canonical_summary':{'estimated_usd_max':100,'requests_max':1000}};return s
 def test_prepaid_atomic_attempts_and_history(self):
  from deploy.modal.cloud_budget import CloudLedger
  s=self.store()
  with patch('modal.Dict.from_name',return_value=s):
   l=CloudLedger()
   with l.reserve('op',.012)as i:l.finish(i,'http-response',{'model':'x','input_tokens':10,'api_key':'NEVER'})
   with l.connect()as c:rows=c.execute('select reserved,status,metadata from attempts where operation=?',('op',)).fetchall()
   self.assertEqual(len(rows),1);self.assertNotIn('NEVER',str(rows));self.assertEqual(l.summary()['cloud_permits_remaining'],29);self.assertEqual(l.summary()['requests_max'],1000)
 def test_budget_lock_and_bound(self):
  from deploy.modal.cloud_budget import CloudLedger
  from v2.budget import BudgetBlocked
  s=self.store()
  with patch('modal.Dict.from_name',return_value=s):
   l=CloudLedger();s.rows['lock']='other'
   with self.assertRaises(BudgetBlocked):
    with l.reserve('op',.01):pass
   del s.rows['lock']
   with self.assertRaises(BudgetBlocked):
    with l.reserve('op',.1):pass
 def test_reference_exact_text_only(self):
  from deploy.modal.gallery import reference
  rows=[{'id':'x','filename':'x.pdf','suggestions':[{'question':'Exact?','reference':12,'unit':'m2','verification':'fixture'}]}]
  with patch('deploy.modal.gallery.catalog',return_value=rows):
   self.assertIsNotNone(reference('x','Exact?'));self.assertIsNone(reference('x','Edited?'))
 def test_preview_validation(self):
  import io,base64
  from PIL import Image
  from deploy.modal.display_assets import validate
  out=io.BytesIO();Image.new('RGB',(50,40),'white').save(out,format='PNG');r=validate({'file_name':'a.png','file_base64':base64.b64encode(out.getvalue()).decode()});self.assertTrue(r['ready']);self.assertTrue(r['preview'].startswith('data:image/png'))
