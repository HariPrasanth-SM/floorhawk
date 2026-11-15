import unittest,json,tempfile,os
from pathlib import Path
from unittest.mock import patch
from qa.common import ROOT
import demo_gpu
class DemoTests(unittest.TestCase):
 def test_live_policy_can_disable_host_vision(self):
  with patch.dict(os.environ,{'PROOFPLAN_HOST_VISION':'0'}):self.assertFalse(demo_gpu.enabled())
 def test_old_host_rejected_before_image_transfer(self):
  with patch('v2.worker_client.request',return_value={'vision':False})as request:
   with self.assertRaisesRegex(RuntimeError,'restart'):demo_gpu.call('/no-source','cubicasa',{})
   self.assertEqual(request.call_count,1)
 def test_actual_gpu_trace_contains_model_input_device(self):
  r=json.loads((ROOT/'results/demo-polish/verification.json').read_text());events=(r.get('window_execution')or[])+(r.get('fixture_execution')or[])
  self.assertTrue(any(e.get('observed_tensor_devices')==['cuda:0']and e.get('peak_gpu_memory_bytes',0)>0 for e in events))
 def test_detection_thresholds_unchanged(self):
  from v2.structural import SETTINGS,SHA256
  self.assertEqual((SETTINGS['conf'],SETTINGS['iou'],SETTINGS['imgsz']),(.25,.5,1024));self.assertEqual(SHA256,'7c86051cc9f620f119ad16ee5c30a7c4893871ec8684897eac02e996d3307506')
if __name__=='__main__':unittest.main()
