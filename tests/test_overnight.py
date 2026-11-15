import unittest,copy,tempfile,json,hashlib
from pathlib import Path
from unittest.mock import patch
from campaign.clock import DEADLINES,effective_target,PUSH_90_BEFORE,admit
from campaign.candidate import apply
from campaign.selector import features,FEATURE_NAMES,proposals,select,VERSION
from campaign.ensemble import instances
class OvernightTests(unittest.TestCase):
 def test_review_schema_failure_is_not_provider_outage(self):
  from campaign.live_adapter import review_failure
  from v2.budget import BudgetBlocked
  self.assertEqual(review_failure(ValueError('schema'),'proposal_validation_and_selection')['status'],'validation_error');self.assertEqual(review_failure(BudgetBlocked('stop'),'provider_review')['status'],'blocked');self.assertEqual(review_failure(RuntimeError('transport'),'provider_review')['status'],'provider_error')
 def test_final_protocol_cannot_receive_reference_or_grading_fields(self):
  from campaign.final_contract import validate_questions
  validate_questions([{'sample_id':'example','question':'How many windows?'}])
  for field in ['answer','reference','expected','correct','grade','path']:
   with self.assertRaises(ValueError):validate_questions([{'sample_id':'example','question':'How many windows?',field:'forbidden'}])
 def test_published_job_sync_never_caches_running_or_new_job(self):
  from deploy.modal.publication import PublishedJobs
  from unittest.mock import Mock
  volume=Mock();cache=PublishedJobs(volume,limit=1);state={'a':{'status':'running'},'b':{'status':'success'}}
  cache.sync('a',state.__getitem__);cache.sync('a',state.__getitem__);self.assertEqual(volume.reload.call_count,2)
  state['a']['status']='success';cache.sync('a',state.__getitem__);cache.sync('a',state.__getitem__);self.assertEqual(volume.reload.call_count,3)
  cache.sync('b',state.__getitem__);self.assertEqual(volume.reload.call_count,4);cache.sync('a',state.__getitem__);self.assertEqual(volume.reload.call_count,5)
 def test_hard_helsinki_deadlines_and_target(self):
  self.assertLess(DEADLINES['optimize'],DEADLINES['deploy']);self.assertLess(DEADLINES['deploy'],DEADLINES['evaluate']);self.assertEqual(effective_target(PUSH_90_BEFORE-1),.9);self.assertEqual(effective_target(PUSH_90_BEFORE+1),.85)
  with patch('campaign.clock.time.time',return_value=DEADLINES['optimize']+1):
   with self.assertRaises(TimeoutError):admit('optimize')
 def fixture(self):
  return {'status':'success','answer':1,'unit':'count','input_kind':'raster','source_sha256':'x','task':{'operation':'count','target':'sink','filters':{},'scope':'drawing'},'evidence':[],'warnings':[]}
 def test_source_and_weight_compatibility(self):
  obs={'status':'success','source_sha256':'wrong','model':{'weight_sha256':'w'},'entities':[]};cfg={'custom_weight_sha256':'w','targets':{'sink':{'confidence':.4,'iou':.5}}}
  with self.assertRaises(ValueError):apply(self.fixture(),obs,cfg)
 def test_no_partial_total_and_count_matches_instances(self):
  obs={'status':'success','source_sha256':'x','model':{'weight_sha256':'w'},'coverage':{'complete':False},'entities':[]};cfg={'custom_weight_sha256':'w','targets':{'sink':{'confidence':.4,'iou':.5}}};self.assertEqual(apply(self.fixture(),obs,cfg)['answer'],1);obs['coverage']['complete']=True;obs['entities']=[{'id':'a','class':'sink','score':.9,'bbox':[0,0,5,5]},{'id':'b','class':'sink','score':.8,'bbox':[1,1,5,5]}];r=apply(self.fixture(),obs,cfg);self.assertEqual(r['answer'],len(r['evidence']));self.assertEqual(r['answer'],1)
 def test_selector_never_generates_a_count(self):
  local=self.fixture();local['task']['target']='bedroom';review={'requested':['bedroom'],'uncertain':[],'entities':[{'id':'r1','class':'bedroom','bbox':[0,0,5,5]},{'id':'r2','class':'bedroom','bbox':[5,5,10,10]}],'model':'g','version':'v','prompt_sha256':'h','generation_seconds':1,'usage':{}};model={'version':VERSION,'features':FEATURE_NAMES,'intercept':0,'learning_rate':.1,'trees':[]};r=select(local,review,[],[10,10],model);self.assertIn(r['answer'],[1,2]);self.assertNotIn('path',FEATURE_NAMES);self.assertFalse(any('reference'in s for s in FEATURE_NAMES))
 def test_no_gemini_score_fabrication(self):
  local=self.fixture();local['task']['target']='bedroom';review={'requested':['bedroom'],'uncertain':[],'entities':[{'id':'a','class':'bedroom','bbox':[0,0,5,5],'score':1}],'model':'g','version':'v','prompt_sha256':'h','generation_seconds':1,'usage':{}};p=proposals(local,review,[]);self.assertNotIn('score',p[1][1]['evidence'][0])
 def test_corroboration_preserves_adjacent_instances(self):
  rt=[{'id':'1','class':'door','bbox':[0,0,10,10],'score':.9},{'id':'2','class':'door','bbox':[12,0,22,10],'score':.9}];r=instances(rt,[],'door','corroborated');self.assertEqual(len(r),2)
 def test_direct_fixture_has_real_observations_and_shared_bundle(self):
  from campaign.live_adapter import direct_fixture
  from qa.common import sha
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'source.png';p.write_bytes(b'fixture bytes');obs={'status':'success','source_sha256':sha(p),'model':{'weight_sha256':'w'},'entities':[{'id':'s','class':'sink','score':.9,'bbox':[0,0,5,5]}],'execution':{'device':'cuda:0','inference_seconds':.1}};cfg={'custom_weight_sha256':'w','targets':{'sink':{'confidence':.4,'iou':.5}}};r=direct_fixture(p,'How many sinks?',self.fixture()['task'],obs,cfg,Path(d)/'out',.2)
   self.assertEqual(r['answer'],1);self.assertEqual(len(r['evidence']),1);self.assertTrue(Path(r['shared_evidence']['path']).is_file());self.assertEqual(r['device'],'cuda:0');self.assertNotIn('reference',json.dumps(r));self.assertEqual(r['previous_local']['status'],'not_run')
   before=sha(Path(r['shared_evidence']['path']));obs['execution']['cache_hit']=True;r2=direct_fixture(p,'How many washbasins?',self.fixture()['task'],obs,cfg,Path(d)/'out',.002);self.assertEqual(sha(Path(r['shared_evidence']['path'])),before);self.assertTrue(r2['timing']['cache_hit']);self.assertEqual(r2['timing']['inference_seconds'],0);self.assertNotEqual(r['question_evidence']['path'],r2['question_evidence']['path'])
if __name__=='__main__':unittest.main()

class NativePDFRecoveryTests(unittest.TestCase):
 def make_pdf(self,folder,printed=False):
  import pymupdf
  path=Path(folder)/'source.pdf';doc=pymupdf.open();p=doc.new_page(width=600,height=400);p.draw_rect(pymupdf.Rect(50,50,250,250),color=(0,0,0),fill=(1,1,1));p.insert_text((110,105),'Storage',fontsize=9);p.insert_text((110,117),'U1.01',fontsize=9)
  if printed:p.insert_text((110,129),'10 m2',fontsize=9)
  p.insert_text((350,350),'1:100',fontsize=9);doc.save(path);doc.close();return path
 def test_prefixed_id_and_printed_area_priority(self):
  from campaign.pdf_quantities import recover
  from qa.router import route
  from qa.common import sha
  with tempfile.TemporaryDirectory()as d:
   path=self.make_pdf(d,True);before=sha(path);r=recover(path);room=next(e for e in r['entities']if e.get('room_number')=='U1.01');self.assertEqual(room['area_m2'],10);self.assertEqual(sha(path),before);self.assertEqual(route('What is the net floor area of room U1.01 in m2?')['filters']['room_number'],'U1.01')
 def test_closed_native_rectangle_at_explicit_scale(self):
  from campaign.pdf_quantities import recover
  with tempfile.TemporaryDirectory()as d:
   path=self.make_pdf(d,False);r=recover(path);room=next(e for e in r['entities']if e.get('room_number')=='U1.01');self.assertAlmostEqual(room['area_m2'],40000*(100*.0254/72)**2,places=5);self.assertIn('room_polygon_points',room)
