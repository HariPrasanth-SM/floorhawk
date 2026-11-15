"""Replay actual saved response shapes through mocks; no HTTP or key access."""
import io,json,tempfile,unittest,warnings
from pathlib import Path
from unittest.mock import Mock
from PIL import Image
from iteration.paired import Engine
class TerminalTests(unittest.TestCase):
 def setup_engine(self,d,data):
  source=Path(d)/'source.png';Image.new('RGB',(100,100),'white').save(source);p=Mock();p.config={};p.v3_sources={};p.base.preprocessing_version='test';p.base.facts.return_value=({'entities':[]},True,.001,'fixture');p.answer.return_value={'request_id':'local','status':'success','answer':400.63,'unit':'m2','task':{'operation':'area'},'evidence':[{'id':'room-1','bbox':[10,10,20,20]}],'warnings':[]};provider=Mock(return_value={'data':data});return source,Engine(p,Path(d)/'bundles',provider),provider
 def test_abstention_with_preview_pixel_region_preserved(self):
  for status in['abstained','unsupported']:
   with self.subTest(status=status),tempfile.TemporaryDirectory()as d:
    data={'status':status,'value':None,'unit':None,'evidence_ids':[],'explanation':'Only one floor is supplied; whole building area is unavailable.','request_region':{'page':1,'bbox':[0,0,1449,2048]}};f,e,provider=self.setup_engine(d,data);r=e.answer(f,'Entire building area?',mode='hybrid');h=r['paired']['hybrid'];self.assertEqual(h['status'],status);self.assertIn('one floor',h['explanation']);self.assertEqual(r['answer'],400.63);self.assertEqual(provider.call_count,1);self.assertEqual(h['model_proposed_regions'],[]);self.assertEqual(len(h['ignored_region_proposals']),1);self.assertIsNotNone(data['request_region']);e.close()
 def test_bad_answer_is_validation_error_not_outage(self):
  with tempfile.TemporaryDirectory()as d:
   data={'status':'answered','value':42,'unit':'m2','evidence_ids':[],'explanation':'Guess','request_region':None};f,e,p=self.setup_engine(d,data);r=e.answer(f,'Area?',mode='hybrid');self.assertEqual(r['paired']['hybrid']['status'],'validation_error');self.assertIn('evidence',r['paired']['hybrid']['explanation']);self.assertEqual(p.call_count,2);e.close()
 def test_optional_out_of_bounds_region_does_not_erase_valid_citation(self):
  with tempfile.TemporaryDirectory()as d:
   data={'status':'answered','value':42,'unit':'m2','evidence_ids':['room-1'],'explanation':'Printed value','request_region':{'page':1,'bbox':[0,0,1449,2048]}};f,e,p=self.setup_engine(d,data);r=e.answer(f,'Area?',mode='hybrid');self.assertEqual(r['paired']['hybrid']['status'],'success');self.assertEqual(r['paired']['hybrid']['model_proposed_regions'],[]);self.assertEqual(p.call_count,1);e.close()
 def test_sdk_warning_fix_keeps_minimal_wire_value(self):
  from v2.gemini import thinking_config,MODEL
  from google.genai import types
  with warnings.catch_warnings(record=True)as recorded:
   warnings.simplefilter('always');config=types.GenerateContentConfig(thinking_config=thinking_config(MODEL));self.assertEqual(config.model_dump(mode='json')['thinking_config']['thinking_level'].lower(),'minimal');self.assertFalse(any('not a valid ThinkingLevel'in str(w.message)for w in recorded))
if __name__=='__main__':unittest.main()
