"""Deterministic geometry fixtures; these are unit tests, not model predictions."""
import tempfile,unittest,fcntl,json
from pathlib import Path
from detector import tile_origins,map_box,suppress,validate_boxes,Detector,ROOT,render
from PIL import Image

class GeometryTests(unittest.TestCase):
 def test_tiles_cover_edges_without_gap(self):
  for length in [389,1024,1234,2000,2730]:
   origins=tile_origins(length,1024,256)
   self.assertEqual(origins[0],0);self.assertEqual(origins[-1]+min(length,1024),length)
   self.assertTrue(all(b-a<=1024 for a,b in zip(origins,origins[1:])))
 def test_crop_coordinates_are_original_pixels(self):
  self.assertEqual(map_box([10,20,40,60],(768,256),2730,2048),[778,276,808,316])
  self.assertEqual(map_box([-10,-10,40,60],(0,0),20,30),[0,0,20,30])
 def test_cross_tile_duplicate_and_nearby_distinct(self):
  boxes=[{'xyxy':[100,10,120,100],'confidence':.9,'class_id':34},
         {'xyxy':[101,10,121,100],'confidence':.7,'class_id':34},
         {'xyxy':[125,10,145,100],'confidence':.8,'class_id':34}]
  kept,removed=suppress(boxes,.45);self.assertEqual(len(kept),2);self.assertEqual(len(removed),1)
 def test_border_fragments_are_not_silently_merged(self):
  # Partial fragments with low IoU can survive. This limitation needs visual review.
  kept,_=suppress([{'xyxy':[0,0,10,100],'confidence':.9,'class_id':34},{'xyxy':[0,0,10,20],'confidence':.8,'class_id':34}],.45)
  self.assertEqual(len(kept),2)
 def test_reviews_reject_invalid_and_count_only_included(self):
  clean=validate_boxes([{'xyxy':[0,0,10,10],'included':True},{'xyxy':[20,20,30,30],'included':False}],100,100)
  self.assertEqual(sum(b['included'] for b in clean),1)
  for coords in [[-1,0,10,10],[0,0,0,1],[0,0,float('nan'),1],[0,0,101,1]]:
   with self.assertRaises(ValueError):validate_boxes([{'xyxy':coords}],100,100)
 def test_lock_rejects_second_inference(self):
  with (ROOT/'cache/inference.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaisesRegex(RuntimeError,'Another FloorHAWK inference'):Detector().predict('unused',{})
 def test_caption_does_not_cover_or_shift_drawing(self):
  with tempfile.TemporaryDirectory() as temp:
   im=Path(temp)/'in.png';target=Path(temp)/'out.png';Image.new('RGB',(389,614),'white').save(im)
   render(im,[{'xyxy':[30,40,100,150],'included':True}],target,'CubiCasa5K (c) 2019 CubiCasa; Kalervo et al., SCIA 2019; CC BY-NC-SA 4.0')
   out=Image.open(target);self.assertEqual(out.width,389);self.assertGreater(out.height,614);self.assertEqual(out.getpixel((30,100)),(219,69,31))
 def test_frozen_groups_and_pixels_disjoint(self):
  dev=[json.loads(x) for x in (ROOT/'manifests/v1/dev.jsonl').read_text().splitlines()];ev=[json.loads(x) for x in (ROOT/'manifests/v1/eval.jsonl').read_text().splitlines()]
  self.assertEqual((len(dev),len(ev)),(20,50));self.assertFalse({r['image_sha256'] for r in dev}&{r['image_sha256'] for r in ev})
  import re
  groups=lambda rows:{re.search(r'-(\d+)\.',r['image']).group(1) for r in rows}
  self.assertFalse(groups(dev)&groups(ev))

if __name__=='__main__':unittest.main()
