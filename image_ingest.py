"""Bounded large-raster ingestion; original bytes remain in the job directory."""
import io,math,threading
from PIL import Image,ImageOps
MAX_SOURCE_PIXELS=100_000_000
MAX_WORKING_PIXELS=8_000_000
MAX_UNCHANGED_PIXELS=30_000_000
Image.MAX_IMAGE_PIXELS=MAX_SOURCE_PIXELS
LOCK=threading.Lock()
def prepare(data):
 import numpy as np
 with LOCK,Image.open(io.BytesIO(data))as raw:
  rw,rh=raw.size
  if min(rw,rh)<16 or rw*rh>MAX_SOURCE_PIXELS or max(rw,rh)>32000:raise ValueError('Use an image with edges between16 and32000 pixels and at most100 megapixels. Larger images must be resized before upload.')
  orientation=int(raw.getexif().get(274,1));m={1:[[1,0,0],[0,1,0],[0,0,1]],2:[[-1,0,rw],[0,1,0],[0,0,1]],3:[[-1,0,rw],[0,-1,rh],[0,0,1]],4:[[1,0,0],[0,-1,rh],[0,0,1]],5:[[0,1,0],[1,0,0],[0,0,1]],6:[[0,-1,rh],[1,0,0],[0,0,1]],7:[[0,-1,rh],[-1,0,rw],[0,0,1]],8:[[0,1,0],[-1,0,rw],[0,0,1]]}.get(orientation,[[1,0,0],[0,1,0],[0,0,1]])
  rotated=orientation in[5,6,7,8];ow,oh=(rh,rw)if rotated else(rw,rh);resize=rw*rh>MAX_UNCHANGED_PIXELS
  ratio=min(1,math.sqrt(MAX_WORKING_PIXELS/(rw*rh)),4096/max(rw,rh))if resize else 1
  target=(max(1,int(ow*ratio)),max(1,int(oh*ratio)))
  # JPEG draft reduces decoding memory where supported. PNG remains source-bounded.
  if resize:raw.draft('RGB',(target[1],target[0])if rotated else target)
  im=ImageOps.exif_transpose(raw);im.thumbnail(target,Image.Resampling.LANCZOS);im=im.convert('RGB');im.load()
  transform=np.diag([im.width/ow,im.height/oh,1])@np.array(m,dtype=float)
  info={'exif_orientation':orientation,'raw_size':[rw,rh],'canonical_size':list(im.size),'resized':resize,'raw_to_canonical_edge_matrix':transform.tolist(),'canonical_to_raw_edge_matrix':np.linalg.inv(transform).tolist(),'coordinates':'Evidence boxes use the EXIF-normalized working image; inverse transform maps to retained original pixels.'}
  return im,info
