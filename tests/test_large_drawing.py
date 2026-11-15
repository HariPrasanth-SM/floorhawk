import unittest
from large_drawing import positions,merge
class TileTests(unittest.TestCase):
 def test_grid_covers_edge_and_overlap(self):
  p=positions(10200);self.assertEqual(p[0],0);self.assertEqual(p[-1]+1536,10200);self.assertTrue(all(b-a<=1536 for a,b in zip(p,p[1:])))
 def test_class_and_location_aware_dedup(self):
  rows=[{'class':'window','bbox':[100,100,200,130],'score':.9},{'class':'window','bbox':[102,101,201,131],'score':.8},{'class':'window','bbox':[210,100,310,130],'score':.8},{'class':'door','bbox':[100,100,200,130],'score':.8}];self.assertEqual(len(merge(rows)),3)
 def test_text_needs_location_not_only_label(self):
  rows=[{'text':'PUMP','bbox':[10,10,50,30]},{'text':'pump','bbox':[11,10,50,30]},{'text':'PUMP','bbox':[100,10,150,30]}];self.assertEqual(len(merge(rows,True)),2)
 def test_offset_roundtrip(self):
  original=[1200+12,2400+24,1200+60,2400+80];scale=.25;preview=[v*scale for v in original];self.assertEqual([v/scale for v in preview],original)
