"""V3 contracts/security/geometry tests. Synthetic fixtures are never scored as model runs."""
import contextlib,io,json,tempfile,unittest,math
from pathlib import Path
from unittest.mock import patch,MagicMock
from types import SimpleNamespace
from PIL import Image
class V3Tests(unittest.TestCase):
 def test_primary_noun_and_quantity_boundaries(self):
  from qa.router import route
  a=route('How many kitchens (including kitchenettes, open kitchens and utility kitchens) are on this floor plan?');self.assertEqual(a['target'],'kitchen');self.assertEqual(a['filters'],{})
  a=route('How many bathrooms or washrooms (e.g. KH, KPH) are on this floor plan, not counting separate WC rooms?');self.assertEqual(a['target'],'bathroom')
  a=route('How many separate WC rooms, excluding bathrooms, are shown?');self.assertEqual(a['target'],'wc_room')
  self.assertEqual(route('What is the surface nette of the apartment?')['filters']['quantity_kind'],'net')
 def test_reference_defaults_remain_compatible(self):
  from qa.raster import CubiParser
  p=CubiParser();self.assertEqual(p.max_edge,512);self.assertEqual(p.rotations,[(0,0),(1,-1),(2,2),(-1,1)]);self.assertEqual(p.threads,4);self.assertTrue(p.ocr)
 def test_fragment_suppression_preserves_adjacent_openings_and_classes(self):
  from v3.dedup import suppress
  es=[{'id':'a','class':'window','bbox':[0,0,100,10],'score':.9},{'id':'fragment','class':'window','bbox':[10,0,40,10],'score':.7},{'id':'adjacent','class':'window','bbox':[100,0,200,10],'score':.8},{'id':'door','class':'door','bbox':[0,0,100,10],'score':.8}]
  kept,removed=suppress(es,'fragments85');self.assertEqual({e['id'] for e in kept},{'a','adjacent','door'});self.assertEqual(removed[0]['entity']['id'],'fragment')
 def test_pdf_normalized_patch_roundtrips_all_rotations(self):
  import pymupdf
  from v3.inventory import answer
  for rotation in (0,90,180,270):
   with pymupdf.open() as d:
    p=d.new_page(width=240,height=130);p.set_rotation(rotation);expected=pymupdf.Rect(20,30,90,70);display=expected*p.rotation_matrix;r=p.rect
    inv={'entities':[{'id':'x','class':'window','normalized_bbox':[display.x0/r.width,display.y0/r.height,display.x1/r.width,display.y1/r.height]}],'uncertain_targets':[],'frame':{'kind':'pdf','rect':list(r),'rotation':rotation,'derotation_matrix':list(p.derotation_matrix)},'version':'unit-fixture','generation':{'reserved_usd':.014},'cache_hit':True}
    got=answer(inv,'window');self.assertEqual(got['answer'],1);self.assertTrue(all(abs(a-b)<1e-6 for a,b in zip(got['evidence'][0]['bbox'],expected)));self.assertIsNone(answer(inv,'unregistered'))
 def test_raster_does_not_answer_model_wide_or_unresolved_floor_scope(self):
  from qa.router import route
  from qa.tools import raster_answer
  from v2.structural import answer
  task=route('Qual è il numero di porte nel modello «Example»?');self.assertEqual(task['operation'],'count');self.assertEqual(task['scope'],'model');self.assertEqual(raster_answer({'entities':[]},task,'')['status'],'abstained')
  with self.assertRaises(ValueError):answer('/nonexistent.png',task)
  task=route('How many windows are on the second floor?');self.assertEqual(raster_answer({'entities':[]},task,'')['status'],'abstained')
 def test_bounded_provider_profiles_and_model_allowlist(self):
  from v2.gemini import generate,ProviderBlocked
  response=SimpleNamespace(text='{"ok":true}',usage_metadata=SimpleNamespace(prompt_token_count=100,candidates_token_count=5,thoughts_token_count=0));fake=MagicMock();fake.__enter__.return_value.models.generate_content.return_value=response
  with patch('v2.gemini.client',return_value=fake) as client,patch('v2.gemini.secret',side_effect=AssertionError('Unit fixture must not read a real secret')):
   r=generate('Unit structured response',{'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok']},model='gemini-3-flash-preview',max_output_tokens=4096,input_token_bound=16384,media_resolution='high');self.assertEqual(r['reserved_usd'],.021);self.assertEqual(client.call_args.kwargs['model'],'gemini-3-flash-preview');self.assertEqual(fake.__enter__.return_value.models.generate_content.call_args.kwargs['config'].media_resolution.value,'MEDIA_RESOLUTION_HIGH')
  with patch('v2.gemini.client') as client:
   with self.assertRaises(ProviderBlocked):generate('unit',{},model='unpriced-unregistered')
   client.assert_not_called()
 def test_large_image_rejected_before_provider_or_secret(self):
  from v2.gemini import generate,ProviderBlocked
  b=io.BytesIO();Image.new('RGB',(2049,16),'white').save(b,format='PNG')
  with patch('v2.gemini.client') as client:
   with self.assertRaises(ProviderBlocked):generate('unit',{},b.getvalue(),input_token_bound=16384)
   client.assert_not_called()
 def test_review_unknown_candidate_id_rejected_not_counted(self):
  from v3.review import review
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);file=root/'unit.png';Image.new('RGB',(100,100),'white').save(file);r={'task':{'operation':'count','target':'window','filters':{},'scope':'drawing'},'evidence':[{'id':'real-proposal','bbox':[10,10,20,20]}]};response={'data':{'keep':['invented-id'],'add':[],'uncertain':False,'note':''}}
   with patch('v3.review.ROOT',root),patch('v3.review.generate',return_value=response):
    with self.assertRaises(ValueError):review(file,'Count windows',r)
 def test_room_fusion_count_and_exclusive_roles_from_actual_regions(self):
  import numpy as np
  from qa.common import sha
  from v3.rooms import predict,ROLES,FEATURE_VERSION
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);file=root/'unit.png';Image.new('RGB',(100,100),'white').save(file);weights=root/'model.json';W=np.zeros((33,7));W[0,1]=10;weights.write_text(json.dumps({'feature_version':FEATURE_VERSION,'roles':ROLES,'coefficients':W.tolist(),'thresholds':{r:.5 for r in ROLES}}));facts={'source_sha256':sha(file),'image_size':[100,100],'entities':[{'id':'r1','kind':'room','class':'bedroom','bbox':[10,10,90,90],'polygon':[[10,10],[90,10],[90,90],[10,90]],'score':None}],'model':{'weights_sha256':'synthetic-unit-fixture'},'preprocessing':{},'timing':{},'cache_hit':True};ocr={'words':[{'text':'MH1','bbox':[30,30,40,40],'ocr_score':.99}],'settings':{},'timing':{},'cache_hit':True}
   with patch('v3.rooms.ROOT',root),patch('v3.rooms.MODEL',weights),patch('v3.rooms.parse',return_value=facts),patch('v3.rooms.ocr_parse',return_value=ocr),patch('v3.rooms.inference_lock',contextlib.nullcontext),patch('v3.rooms.sha',side_effect=lambda p:sha(p) if Path(p).exists() else 'synthetic-source-sha'):
    a=predict(file,'bedroom');b=predict(file,'wc_room');self.assertEqual(a['answer'],len(a['evidence']));self.assertEqual(a['answer'],1);self.assertEqual(b['answer'],0);self.assertEqual(a['calculation_trace'][0]['ids'],[e['id'] for e in a['evidence']]);self.assertEqual(a['evidence'][0]['bbox'],[10,10,90,90]);weights.unlink()
    with self.assertRaises(FileNotFoundError):predict(file,'bedroom')
 def test_production_modules_have_no_reference_file_access(self):
  root=Path(__file__).resolve().parent
  for name in ('pipeline','layouts','rooms','wash','raster','weak_boxes','cross_boxes','inventory','review'):
   self.assertNotIn('.answers.jsonl',(root/'v3'/(name+'.py')).read_text())
if __name__=='__main__':unittest.main()
