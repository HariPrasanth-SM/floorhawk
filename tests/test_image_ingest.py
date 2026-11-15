import io,unittest
from PIL import Image
from image_ingest import prepare
class IngestTests(unittest.TestCase):
 def test_reported_large_image_is_resized(self):
  image=Image.new('L',(10200,6600),255);b=io.BytesIO();image.save(b,format='PNG');im,info=prepare(b.getvalue());self.assertLessEqual(im.width*im.height,8_000_000);self.assertEqual(info['raw_size'],[10200,6600]);self.assertTrue(info['resized']);self.assertEqual(im.mode,'RGB')
 def test_small_dimensions_preserved(self):
  b=io.BytesIO();Image.new('RGB',(120,80)).save(b,format='PNG');im,info=prepare(b.getvalue());self.assertEqual(im.size,(120,80));self.assertFalse(info['resized'])
 def test_rotated_mapping(self):
  import numpy as np
  b=io.BytesIO();im=Image.new('RGB',(120,80));exif=im.getexif();exif[274]=6;im.save(b,format='JPEG',exif=exif);out,info=prepare(b.getvalue());self.assertEqual(out.size,(80,120));m=np.array(info['raw_to_canonical_edge_matrix']);inverse=np.array(info['canonical_to_raw_edge_matrix']);np.testing.assert_allclose(inverse@m,np.eye(3))
