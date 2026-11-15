import unittest
from presentation import selected,catalog
class PresentationTests(unittest.TestCase):
 def test_hybrid_resolves_cumulative_not_local_boxes(self):
  j={'prediction':{'evidence':[{'id':'local','bbox':[0,0,1,1]}],'cumulative_evidence':{'evidence':[{'id':'custom:1','bbox':[5,5,9,9],'origin_model':'custom_yolo'}]},'paired':{'hybrid':{'status':'success','evidence_ids':['custom:1']}}}}
  self.assertEqual(selected(j,'hybrid')[0]['bbox'],[5,5,9,9]);self.assertEqual(selected(j,'local')[0]['id'],'local')
 def test_overview_is_not_fake_instance(self):
  j={'prediction':{'paired':{'hybrid':{'status':'success','answer':4,'evidence_ids':['source-view-page-1']}}}}
  rows=selected(j,'hybrid');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['kind'],'source_overview');self.assertNotIn('bbox',rows[0])
 def test_proposal_unverified_and_missing_id_not_fabricated(self):
  j={'prediction':{'paired':{'hybrid':{'status':'success','evidence_ids':['missing'],'model_proposed_regions':[{'id':'proposal','bbox':[1,2,3,4]}]}}}}
  rows=selected(j,'hybrid');self.assertEqual(len(rows),1);self.assertFalse(rows[0]['verified_local_evidence'])
