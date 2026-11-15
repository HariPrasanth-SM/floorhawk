"""V2 policy/security tests use synthetic data, never real credential values."""
import tempfile,unittest,time,json,socket
from pathlib import Path
from unittest.mock import patch
from v2.budget import Ledger,BudgetBlocked
from v2.supervisor import Admission
class V2Tests(unittest.TestCase):
 def test_budget_persistent_exhaustion(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'ledger.sqlite';a=Ledger(p,1,.01)
   with a.reserve('synthetic',.01):pass
   with self.assertRaises(BudgetBlocked):
    with Ledger(p,1,.01).reserve('second',.01):self.fail('sent')
   self.assertEqual(Ledger(p,1,.01).summary()['requests_reserved'],1)
 def test_budget_failed_stays_spent(self):
  with tempfile.TemporaryDirectory() as d:
   a=Ledger(Path(d)/'ledger',10,1)
   with self.assertRaises(RuntimeError):
    with a.reserve('synthetic',.01):raise RuntimeError('simulated timeout')
   self.assertEqual(a.summary()['estimated_usd_reserved'],.01)
 def test_one_cloud_inflight(self):
  with tempfile.TemporaryDirectory() as d:
   a=Ledger(Path(d)/'ledger',10,1)
   with a.reserve('first',.01):
    with self.assertRaises(BudgetBlocked):
     with a.reserve('second',.01):self.fail('sent')
 def test_resource_pressure_recovery_and_loss(self):
  a=Admission();s={'disk_free_bytes':20*2**30,'cpu_percent':20,'ram_used_percent':40,'gpu_available':True,'gpu_memory_percent':10,'gpu_utilization_percent':0}
  self.assertEqual(a.check(s,True,0),'admit');self.assertEqual(a.check(dict(s,ram_used_percent=79),True,1),'shed');self.assertEqual(a.check(dict(s,cpu_percent=75),True,2),'pause');self.assertEqual(a.check(s,True,3),'pause');self.assertEqual(a.check(s,True,18),'admit');self.assertEqual(a.check(dict(s,gpu_available=False),True),'telemetry-unavailable')
 def test_gpu_single_spike_is_not_kill(self):
  a=Admission();s={'disk_free_bytes':20*2**30,'cpu_percent':20,'ram_used_percent':40,'gpu_available':True,'gpu_memory_percent':40,'gpu_utilization_percent':100}
  self.assertEqual(a.check(s,True,0),'admit');self.assertEqual(a.check(s,True,11),'pause')
 def test_ledger_metadata_allowlist(self):
  with tempfile.TemporaryDirectory() as d:
   a=Ledger(Path(d)/'ledger',10,1)
   with a.reserve('test',.01) as ident:a.finish(ident,'ok',{'api_key':'SYNTHETIC_SECRET_SENTINEL','model':'test'})
   self.assertNotIn(b'SYNTHETIC_SECRET_SENTINEL',a.path.read_bytes())
 def test_local_no_provider_or_cloud_cache(self):
  from v2.pipeline import Pipeline
  from qa.common import ROOT
  p=Pipeline(structural=False);p.local_routing=False
  f=ROOT.parent/'datasets/junction-dataset/data/ifc_bench/fzk_house_arc.ifc'
  with patch('socket.socket.connect',side_effect=AssertionError('network denied')):
   r=p.answer(f,'How many windows are in this IFC model?',mode='local')
  self.assertEqual(r['status'],'success');self.assertEqual(r['cloud']['status'],'off');self.assertEqual(r['execution_mode'],'local')
 def test_generated_filter_not_silently_ignored(self):
  from v2.routing import validate_routed
  base={'operation':'area','target':'room','filters':{'room':'1.05'},'scope':'drawing','requested_unit':'m2'}
  with self.assertRaises(ValueError):validate_routed(base)
  base['filters']={'room_number':'1.05'};self.assertEqual(validate_routed(base)['filters']['room_number'],'1.05')
 def test_room_labels_unique_and_ambiguous(self):
  from v2.ocr import associate
  room={'id':'a','polygon':[[0,0],[100,0],[100,100],[0,100]]};words=[{'id':'w1','text':'MH','bbox':[20,20,30,30]},{'id':'w2','text':'MH','bbox':[40,40,50,50]}]
  matched,amb=associate(words,[room],'bedroom');self.assertEqual(len(matched),1);self.assertEqual(amb,[])
  matched,amb=associate(words,[room,dict(room,id='b')],'bedroom');self.assertFalse(matched);self.assertEqual(len(amb),2)
 def test_cloud_coordinate_transform_and_rejection(self):
  from v2.pipeline import Pipeline
  from v2.gemini import MODEL
  from PIL import Image
  from qa.common import sha
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'fixture.png';Image.new('RGB',(200,100),'white').save(f)
   task={'operation':'count','target':'balcony','scope':'drawing','filters':{}}
   def result():return {'source_sha256':sha(f),'evidence':[],'local_answer':{'evidence':[]},'task':task,'cloud':{},'tool_revisions':{},'warnings':[],'route':'test','route_decisions':[]}
   response={'data':{'objects':[{'id':'one','region_id':'page-1','target':'balcony','bbox_1000_yxyx':[100,200,500,800],'text':'PARVEKE'}],'proposal_usable':True,'caveat':'synthetic test'},'model':MODEL,'reserved_usd':.02}
   p=Pipeline(structural=False,ocr=False);r=result()
   with patch('v2.gemini.generate',return_value=response),patch('v2.pipeline.write_json'):
    p.repair(f,'Synthetic coordinate fixture unique-v2-8673',r)
   self.assertEqual(r['answer'],1);self.assertEqual(r['evidence'][0]['bbox'],[40,10,160,50]);self.assertEqual(len(r['evidence_revisions'][0]['original']),0)
   response['data']['objects'][0]['bbox_1000_yxyx']=[100,200,1500,800]
   with patch('v2.gemini.generate',return_value=response),patch('v2.pipeline.write_json'),self.assertRaises(ValueError):p.repair(f,'Synthetic invalid coordinate fixture-8673',result())
 def test_cloud_disabled_no_transmission(self):
  from v2.pipeline import Pipeline
  from qa.common import ROOT
  p=Pipeline(structural=False,ocr=False);p.cloud_enabled=False
  f=ROOT.parent/'datasets/junction-dataset/data/ifc_bench/fzk_house_arc.ifc'
  with patch('v2.gemini.generate',side_effect=AssertionError('provider called')):
   r=p.answer(f,'What is the net area of this IFC model?',mode='hybrid')
  self.assertEqual(r['cloud']['status'],'disabled-before-transmission')
 def test_replay_imports_no_model_or_provider(self):
  import subprocess,sys
  code="import v2.replay,sys; assert not any(m in sys.modules for m in ('torch','transformers','google.genai','qa.pipeline','v2.gemini'))"
  subprocess.run([sys.executable,'-c',code],check=True)
 def test_provider_budget_block_preserves_actionable_reason(self):
  from v2.gemini import generate
  with patch('v2.gemini.client',side_effect=BudgetBlocked('Global Gemini allowance exhausted')):
   with self.assertRaisesRegex(BudgetBlocked,'allowance exhausted'):generate('Synthetic test',{'type':'object','properties':{}},operation='mock-only')
 def test_offline_blocks_dns_sockets_and_restores(self):
  import socket
  from v2.offline import local_network_guard,OfflineViolation
  original=socket.socket.connect
  with local_network_guard() as attempts:
   self.assertTrue(socket.getaddrinfo('127.0.0.1',80))
   with self.assertRaises(OfflineViolation):socket.getaddrinfo('example.com',443)
   with socket.socket() as s:
    with self.assertRaises(OfflineViolation):s.connect(('8.8.8.8',443))
   self.assertEqual(len(attempts),2)
  self.assertIs(socket.socket.connect,original)
 def test_manual_app_service_survives_build_deadline_only(self):
  from v2.supervisor import run
  from v2.policy import ROOT,STATE
  import json
  from unittest.mock import MagicMock
  deadline=json.loads((STATE/'preflight.json').read_text())['implementation_deadline_unix'];healthy={'cpu_percent':10,'ram_used_percent':40,'disk_free_bytes':20*2**30,'gpu_available':True,'gpu_memory_percent':10,'gpu_utilization_percent':0};child=MagicMock();child.poll.return_value=0;child.returncode=0;child.pid=123456
  command=[str(ROOT/'.venv/bin/python'),'app.py']
  with patch('v2.supervisor.time.time',return_value=deadline+60),patch('v2.supervisor.sample',return_value=healthy),patch('v2.supervisor.subprocess.Popen',return_value=child) as popen:
   with self.assertRaisesRegex(RuntimeError,'window expired'):run(command)
   self.assertEqual(run(command,service=True),0)
   with self.assertRaisesRegex(RuntimeError,'foreground'):run([str(ROOT/'.venv/bin/python'),'-m','v2.benchmark'],service=True)
 def test_gpu_admission_accounts_for_other_processes(self):
  from v2.worker_client import request
  telemetry={'gpu_available':True,'gpu_total_mib':8188,'gpu_used_mib':4000}
  with patch('v2.supervisor.fresh_host',return_value=telemetry):
   with self.assertRaisesRegex(RuntimeError,'including other processes'):request({'mode':'route','question':'Synthetic admission test'})
if __name__=='__main__':unittest.main()
