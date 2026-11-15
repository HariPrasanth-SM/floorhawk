"""Focused saved-artifact checks. Never runs inference or reads secret material."""
import json,sqlite3,tempfile,unittest,struct
from pathlib import Path
from inspection import analytics,assets
from inspection.store import Store,token
from qa.common import ROOT
class AnalyticsTests(unittest.TestCase):
 def setUp(self):self.g={'sample_id':'x','path':'test.png','question':'How many windows?','answer':7,'unit':'count','type':'count','category':'count_windows'}
 def test_success_is_not_correctness(self):
  self.assertEqual(analytics.outcome(self.g,{'status':'success','answer':5,'unit':'count'})[0],'Incorrect')
 def test_outcomes_are_exclusive(self):
  for p,label in [(None,'Not recorded'),({'status':'abstained'},'Abstained'),({'status':'unsupported'},'Unsupported'),({'status':'failed'},'Execution error'),({'status':'success','answer':None},'Execution error'),({'status':'success','answer':7,'unit':'count'},'Correct')]:self.assertEqual(analytics.outcome(self.g,p)[0],label)
 def test_text_ungraded(self):
  g=dict(self.g,type='text',answer='oak');self.assertEqual(analytics.outcome(g,{'status':'success','answer':'pine'})[0],'Answered but ungraded')
 def test_zero_no_relative_error(self):
  row=analytics.make_row('test','local',dict(self.g,answer=0),{'status':'success','answer':1,'unit':'count'});s=analytics.summarize([row]);self.assertEqual(s['quantities']['count']['relative_nonzero_n'],0)
 def test_no_ocr_inference_from_question(self):self.assertEqual(analytics.ocr_info({'task':{'operation':'text'}}),('other_or_unknown','unknown'))
 def test_totals_left_join(self):
  s=json.loads((ROOT/'results/inspection/summary.json').read_text());p=s['primary_local'];self.assertEqual(sum(p['outcomes'].values()),9544);self.assertEqual(p['correct']+p['incorrect']+p['answered_ungraded'],p['answered']);self.assertEqual(s['primary_hybrid_absent']['not_recorded'],9544);self.assertEqual(s['groups']['format']['SVG']['total'],0);self.assertEqual(sum(r['recorded']for r in s['runs']),100805)
 def test_source_versions_and_pair(self):
  s=Store();self.assertEqual(s.cases('v3-release-quick','hybrid')['cases'][0]['outcome'],'Not recorded');self.assertTrue(all(r['recorded']for r in s.cases('v3-frozen40-comparison','hybrid')['cases']));self.assertEqual(s.cases('v3-release-quick','local','missing')['total'],0)
 def test_empty_filters(self):self.assertEqual(Store().cases('v3-release-quick','local',datatype='SVG')['total'],0)
 def test_missing_image_does_not_erase_answer(self):
  s=Store();case=s.cases('v3-release-quick','local','correct')['cases'][0];from unittest.mock import patch
  with patch.object(s,'source',return_value=ROOT/'cache/inspection-assets/does-not-exist.png'):
   j=s.job(case['id']);self.assertIsNotNone(j['prediction']['answer']);self.assertFalse(j['replay']['missing_recording']);self.assertFalse(j['replay']['source_available']);self.assertEqual(j['review']['boxes'],[])
 def test_saved_answer_snapshot_if_record_unavailable(self):
  s=Store();case=s.cases('v3-release-quick','local','correct')['cases'][0];from unittest.mock import patch
  with patch('pathlib.Path.open',side_effect=OSError('test record unavailable')):
   _,_,row,p=s.lookup(case['id']);self.assertEqual(p['answer'],row['answer']);self.assertTrue(p['indexed_snapshot_only'])
class TranslationTests(unittest.TestCase):
 def test_translation_pairs_same_drawing_task_and_unit(self):
  from inspection.translations import PATH
  data=json.loads(PATH.read_text());gold={q['sample_id']:q for q in (json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').read_text().splitlines())}
  self.assertEqual(len(data['entries']),3202)
  for id,t in data['entries'].items():
   q,e=gold[id],gold[t['english_sample_id']];self.assertEqual(q['path'],e['path']);self.assertEqual(q['category'],e['category']);self.assertEqual(q['type'],e['type']);self.assertEqual(q['unit'],e['unit']);self.assertEqual(t['english'],e['question']);self.assertNotIn('answer',t)
 def test_free_form_translation_unavailable(self):
  from inspection.translations import for_question
  self.assertIsNone(for_question({'sample_id':'missing','question':'anything','path':'x'}))
class RenderingTests(unittest.TestCase):
 def test_svg_scripts_external_resources_removed(self):
  raw=b'<svg xmlns="http://www.w3.org/2000/svg" onload="x()"><script>alert(1)</script><image href="http://example.org/a"/><use href="http://example.org/b"/><rect fill="url(https://example.org/c)"/><foreignObject/><path onclick="x()" d="M0 0L2 2"/></svg>';out=assets.safe_svg(raw);self.assertNotIn(b'example.org',out);self.assertNotIn(b'onclick',out);self.assertNotIn(b'script',out);self.assertIn(b'path',out)
 def test_svg_entities_rejected(self):
  with self.assertRaises(ValueError):assets.safe_svg(b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg/>')
 def test_svg_viewbox_mapping(self):
  with tempfile.TemporaryDirectory()as d:
   source=Path(d)/'test.svg';source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="10 20 100 50"><rect x="20" y="30" width="10" height="10"/></svg>');pages=assets.page_info(source);b=assets.boxes_for({'evidence':[{'bbox':[20,30,30,40]}]},pages,source)[0]['xyxy'];self.assertAlmostEqual(b[0],140);self.assertAlmostEqual(b[1],140)
 def test_rotated_pdf_source_transform(self):
  import pymupdf
  with tempfile.TemporaryDirectory()as d:
   source=Path(d)/'test.pdf'
   with pymupdf.open()as doc:
    page=doc.new_page(width=600,height=800);page.draw_rect(pymupdf.Rect(120,180,240,220),color=(0,0,1),fill=(0,0,1));page.set_cropbox(pymupdf.Rect(50,80,550,700));page.set_rotation(90);doc.save(source)
   pages=assets.page_info(source);b=assets.boxes_for({'evidence':[{'bbox':[70,100,190,140]}]},pages,source)[0]['xyxy'];dest,meta=assets.crop(source,1,b,pages[0]);self.assertEqual(meta['source_rotation'],90)
   for a,v in zip(meta['unrotated_evidence_bbox'],[70,100,190,140]):self.assertAlmostEqual(a,v,places=3)
   from PIL import Image
   im=Image.open(dest);blue=sum(1 for r,g,b in im.getdata()if b>180 and r<50 and g<50);self.assertGreater(blue,im.width*im.height*.15);self.assertTrue(meta['original_crop_render'])
 def test_ifc_mapping_is_actual(self):
  import ifcopenshell
  entries=json.loads((ROOT/'results/inspection/ifc-precomputed.json').read_text());self.assertEqual(len(entries),4)
  from inspection.ifc_geometry import CACHE,key
  # Known saved live FZK model; use source from the registered geometry manifest.
  inputs=json.loads((ROOT/'results/inspection/ifc-inputs.json').read_text());source=next(ROOT.parent/'datasets/junction-dataset'/p for p in inputs if 'fzk_house' in str(p));meta=json.loads((CACHE/key(source)/'metadata.json').read_text());model=ifcopenshell.open(str(source));self.assertEqual(meta['meshes'],107)
  raw=(CACHE/key(source)/'model.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);self.assertEqual(len(gltf['nodes']),107)
  for m in meta['mesh_mapping']:self.assertEqual(model.by_guid(m['guid']).id(),m['step_id']);self.assertEqual(gltf['nodes'][m['node']]['extras']['ifc_guid'],m['guid'])
if __name__=='__main__':unittest.main()
