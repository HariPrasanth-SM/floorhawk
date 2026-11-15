"""Pure supplied-model adapter contracts; no real forward/provider traffic."""
import os,tempfile,unittest
from unittest.mock import patch
from custom_detector import RAW_CLASSES,entities_from_rows,counts_for,answer,_device
class CustomDetectorTests(unittest.TestCase):
 def test_boxes_are_source_pixels_not_rescaled_again(self):
  rows=entities_from_rows([[12.,24.,80.,100.]],[4.],[.8],dict(enumerate(RAW_CLASSES)),[200,300],'source')
  self.assertEqual(rows[0]['bbox'],[12,24,80,100]);self.assertEqual(rows[0]['class'],'window');self.assertEqual(rows[0]['original_class'],'window')
 def test_native_mapping_and_count_groups(self):
  rows=entities_from_rows([[0,0,10,10],[20,0,30,10],[40,0,50,10],[60,0,70,10]],[7,3,2,5],[.9]*4,RAW_CLASSES,[100,100],'s');counts,groups=counts_for(rows)
  self.assertEqual(counts['toilet_fixture'],1);self.assertEqual(groups['shower_bath'],2)
  self.assertEqual(answer({'entities':rows,'model':{},'warnings':[]},'sauna')['status'],'unsupported')
 def test_no_class_guess_or_invalid_vectors(self):
  with self.assertRaises(ValueError):entities_from_rows([[0,0,10,10]],[99],[.9],RAW_CLASSES,[100,100],'s')
  with self.assertRaises(ValueError):entities_from_rows([[0,0,float('nan'),10]],[0],[.9],RAW_CLASSES,[100,100],'s')
  with self.assertRaises(ValueError):entities_from_rows([[0,0,10,10]],[0],[1.2],RAW_CLASSES,[100,100],'s')
 def test_class_order_is_checked(self):
  with self.assertRaises(ValueError):entities_from_rows([],[],[],list(reversed(RAW_CLASSES)),[100,100],'s')
 def test_cuda_requires_host_queue(self):
  with patch.dict(os.environ,{'PROOFPLAN_IN_HOST':'0'}):
   with self.assertRaises(ValueError):_device('0')
  with patch.dict(os.environ,{'PROOFPLAN_IN_HOST':'1'}):self.assertEqual(_device('0'),'cuda:0')
if __name__=='__main__':unittest.main()
