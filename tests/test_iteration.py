import unittest,tempfile,json,threading,time,sys
from pathlib import Path
from unittest.mock import Mock,patch
from iteration.paired import Engine,validate
from evaluation.text import score
class PairTests(unittest.TestCase):
 def engine(self,d):
  p=Mock();p.config={};p.v3_sources={};p.base.preprocessing_version='test';p.base.facts.return_value=({'entities':[{'id':'one','bbox':[0,0,10,10]}]},False,.1,'cache');p.answer.return_value={'request_id':'test','status':'success','answer':1,'unit':'count','evidence':[{'id':'one','bbox':[0,0,10,10]}],'task':{'operation':'count','target':'window','filters':{}},'warnings':[]};return Engine(p,Path(d)/'bundles',provider=Mock(side_effect=RuntimeError('provider fails'))),p
 def test_local_extract_once_and_provider_failure_preserves_local(self):
  with tempfile.TemporaryDirectory()as d:
   f=Path(d)/'input.ifc';f.write_text('fixture');e,p=self.engine(d);a=e.answer(f,'How many?',mode='hybrid');b=e.answer(f,'Count windows',mode='local');self.assertEqual(p.base.facts.call_count,1);self.assertEqual(a['answer'],1);self.assertEqual(a['paired']['hybrid']['status'],'provider_error');self.assertEqual(e.provider.call_count,1);self.assertEqual(a['shared_evidence']['sha256'],b['shared_evidence']['sha256']);e.close()
 def test_local_no_provider_and_reference_free(self):
  with tempfile.TemporaryDirectory()as d:
   f=Path(d)/'input.ifc';f.write_text('fixture');e,p=self.engine(d);r=e.answer(f,'Count',mode='local');e.provider.assert_not_called();payload=Path(r['shared_evidence']['path']).read_text();self.assertNotIn('reference',payload);self.assertNotIn('expected',payload);e.close()
 def test_invalid_id_unit_numeric(self):
  l={'task':{'operation':'count'},'unit':'count'};data={'status':'answered','value':1,'unit':'count','evidence_ids':['one'],'explanation':'Observed','request_region':None};validate(data,l,{'one'})
  for field,value in [('value',True),('value',1.5),('unit','m2'),('evidence_ids',['unknown'])]:
   with self.assertRaises(ValueError):validate(dict(data,**{field:value}),l,{'one'})
 def test_budget_two_slots_atomic_cap(self):
  from v2.budget import Ledger,BudgetBlocked
  with tempfile.TemporaryDirectory()as d:
   l=Ledger(Path(d)/'ledger.sqlite',requests=2,dollars=.03);errors=[]
   with l.reserve('first',.01,concurrency=2):
    with l.reserve('second',.01,concurrency=2):
     with self.assertRaises(BudgetBlocked):
      with l.reserve('third',.01,concurrency=2):pass
   self.assertEqual(l.summary()['requests_reserved'],2)
   with self.assertRaises(BudgetBlocked):
    with l.reserve('cap',.01,concurrency=2):pass
 def test_two_cloud_jobs_max_and_no_reference_payload(self):
  from concurrent.futures import ThreadPoolExecutor
  with tempfile.TemporaryDirectory()as d:
   f=Path(d)/'input.ifc';f.write_text('fixture');e,p=self.engine(d);active=0;peak=0;lock=threading.Lock();prompts=[];operations=[]
   def provider(prompt,*a,**kw):
    nonlocal active,peak
    with lock:active+=1;peak=max(peak,active);prompts.append(prompt);operations.append(kw['operation'])
    time.sleep(.05)
    with lock:active-=1
    return {'data':{'status':'answered','value':1,'unit':'count','evidence_ids':['one'],'explanation':'Observed','request_region':None}}
   e.provider=provider;r=e.local(f,'Count');r['expected']='PRIVATE-REFERENCE';r['grade']={'passed':True}
   with ThreadPoolExecutor(max_workers=4)as pool:answers=list(pool.map(lambda _:e.hybrid(f,'Count',r),range(4)))
   self.assertEqual(peak,2);self.assertEqual(len(set(operations)),4);self.assertTrue(all(a['status']=='success'for a in answers));self.assertNotIn('PRIVATE-REFERENCE',''.join(prompts));self.assertNotIn('"passed"',''.join(prompts));e.close()
 def test_optional_proposal_does_not_become_verified_evidence(self):
  with tempfile.TemporaryDirectory()as d:
   from PIL import Image
   f=Path(d)/'input.png';Image.new('RGB',(20,20),'white').save(f);e,p=self.engine(d);e.provider=lambda *a,**k:{'data':{'status':'answered','value':1,'unit':'count','evidence_ids':['one'],'explanation':'Observed','request_region':{'page':1,'bbox':[0,0,10,10]}}};r=e.answer(f,'Count',mode='hybrid');self.assertEqual(r['paired']['hybrid']['status'],'success');self.assertFalse(r['paired']['hybrid']['model_proposed_regions'][0]['verified_local_evidence']);self.assertEqual(len(r['evidence']),1);e.close()
class RuntimeTests(unittest.TestCase):
 def test_missing_default_ledger_fails_closed(self):
  from v2.budget import Ledger,BudgetBlocked
  with tempfile.TemporaryDirectory()as d,patch('v2.budget.BUDGET_LEDGER',Path(d)/'missing.sqlite'):
   with self.assertRaises(BudgetBlocked):Ledger()
   self.assertFalse((Path(d)/'missing.sqlite').exists())
 def test_results_root_does_not_reset_lifetime_ledger(self):
  import os,subprocess
  from runtime_paths import BUDGET_LEDGER
  with tempfile.TemporaryDirectory()as d:
   env=dict(os.environ,PROOFPLAN_RESULTS_ROOT=d)
   observed=subprocess.check_output([sys.executable,'-c','from runtime_paths import BUDGET_LEDGER;print(BUDGET_LEDGER)'],env=env,text=True).strip();self.assertEqual(observed,str(BUDGET_LEDGER))
class TextTests(unittest.TestCase):
 def test_equivalents(self):self.assertTrue(score('IFC 2x3','ifc2x3.','scalar')['passed'])
 def test_substrings_and_exhaustive_guesses_rejected(self):
  self.assertFalse(score('oak','oak, steel, concrete','scalar')['passed']);self.assertFalse(score(['oak'],['oak','steel'],'set')['passed']);self.assertFalse(score('oak','cloak','scalar')['passed'])
 def test_ordered_list_remains_ungraded(self):
  from evaluation.text import rule_for
  self.assertEqual(rule_for('List the names',['A','B']),'set');self.assertEqual(rule_for('Give the ordered sequence',['A','B']),'free_form')
 def test_sets_and_free_form(self):
  self.assertEqual(score(['A','B'],['b','a'],'set')['f1'],1);self.assertFalse(score('Narrative','Narrative','free_form')['graded'])
if __name__=='__main__':unittest.main()
