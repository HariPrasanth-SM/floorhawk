from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Official CubiCasa reference inference and polygon reconstruction, without annotation sidecars."""
import importlib.util,json,math,sys,time,subprocess,io
from pathlib import Path
from .common import ROOT,sha
CUBI_REV='c34440266665a11f4484eb06cd2e4b7d72ad76c1'
WEIGHT_SHA='dd20b4e1bf1d670f2125107b079df06958b1ccd36e49a464ab739aeb00b8e7a2'
ROOMS=['background','outdoor','wall','kitchen','living_room','bedroom','bath','entry','railing','storage','garage','undefined']
ICONS=['background','window','door','closet','electrical_appliance','toilet_fixture','sink','sauna_bench','fireplace','bathtub','chimney']

def ocr_image(image,max_edge=1800):
 import csv
 from PIL import Image,ImageOps
 im=ImageOps.exif_transpose(Image.open(image)).convert('RGB');w,h=im.size;im.thumbnail((max_edge,max_edge));scale=[w/im.width,h/im.height];buf=io.BytesIO();im.save(buf,format='PNG')
 p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','11','tsv'],input=buf.getvalue(),capture_output=True,timeout=45)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 words=[]
 for r in csv.DictReader(io.StringIO(p.stdout.decode()),delimiter='\t'):
  if not r['text'].strip() or float(r['conf'])<30:continue
  x,y,bw,bh=[int(r[k]) for k in ['left','top','width','height']]
  words.append({'text':r['text'],'bbox':[x*scale[0],y*scale[1],(x+bw)*scale[0],(y+bh)*scale[1]],'ocr_score':float(r['conf']),'coordinate_system':'original image pixels','method':'Tesseract eng sparse text'})
 return words

class CubiParser:
 def __init__(self,device='cpu',max_edge=512,rotations=None,threads=4,ocr=True):
  self.device=device;self.max_edge=max_edge;self.model=None;self.rotations=rotations if rotations is not None else [(0,0),(1,-1),(2,2),(-1,1)];self.threads=threads;self.ocr=ocr
 def parse(self,path):
  import torch,numpy as np
  from PIL import Image,ImageOps
  import torch.nn.functional as F
  sys.path.insert(0,str(MODEL_ROOT/'cubicasa-compatible'))
  from floortrans.models.hg_furukawa_original import hg_furukawa_original
  from floortrans.loaders import RotateNTurns
  from floortrans.post_prosessing import split_prediction,get_polygons
  weights=MODEL_ROOT/'cubicasa-model.pkl'
  if not weights.exists():raise RuntimeError('Official CubiCasa weights missing. Run .venv/bin/python assets.py cubi.')
  if sha(weights)!=WEIGHT_SHA:raise RuntimeError('Official CubiCasa weight checksum mismatch')
  torch.set_num_threads(self.threads);torch.manual_seed(0)
  dev='cuda:0' if self.device=='0' else 'cpu'
  if dev!='cpu' and not torch.cuda.is_available():raise RuntimeError('CUDA unavailable; use --device cpu')
  t=time.perf_counter();cold=self.model is None
  if cold:
   # Full strict state loading overwrites every parameter; MPII initialization is unnecessary.
   self.model=hg_furukawa_original(44)
   self.model.load_state_dict(torch.load(weights,map_location='cpu',weights_only=False)['model_state'],strict=True);self.model.eval()
  self.model.to(dev);load=time.perf_counter()-t
  im=ImageOps.exif_transpose(Image.open(path)).convert('RGB');w,h=im.size;factor=min(1,self.max_edge/max(w,h));pw=max(128,round(w*factor));ph=max(128,round(h*factor))
  import cv2
  rgb=cv2.resize(np.asarray(im),(pw,ph),interpolation=cv2.INTER_LINEAR)
  image=torch.from_numpy(rgb.transpose(2,0,1).copy()).float().unsqueeze(0).to(dev);image=2*(image/255.)-1
  if dev!='cpu':torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize()
  rot=RotateNTurns();predictions=[];t=time.perf_counter()
  with torch.inference_mode():
   for forward,back in self.rotations:
    pred=self.model(rot(image,'tensor',forward));pred=rot(pred,'tensor',back);pred=rot(pred,'points',back);pred=F.interpolate(pred,size=(ph,pw),mode='bilinear',align_corners=True);predictions.append(pred[0].cpu())
   prediction=torch.stack(predictions).mean(0,keepdim=True)
  if dev!='cpu':torch.cuda.synchronize()
  inference=time.perf_counter()-t;peak=torch.cuda.max_memory_allocated() if dev!='cpu' else None
  if dev!='cpu'and not getattr(self,'keep_gpu',False):self.model.cpu();torch.cuda.empty_cache()
  t=time.perf_counter();heat,rooms,icons=split_prediction(prediction,(ph,pw),[21,12,11]);raw_room=rooms.argmax(0);raw_icon=icons.argmax(0)
  polygons,types,room_polygons,room_types=get_polygons((heat,rooms.copy(),icons),.2,[1,2])
  entities=[]
  def entity(poly,cls,kind,score=None):
   coords=np.asarray(poly,dtype=float);coords[:,0]*=w/pw;coords[:,1]*=h/ph;coords[:,0]=np.clip(coords[:,0],0,w);coords[:,1]=np.clip(coords[:,1],0,h)
   bounds=[float(coords[:,0].min()),float(coords[:,1].min()),float(coords[:,0].max()),float(coords[:,1].max())]
   if bounds[0]>=bounds[2] or bounds[1]>=bounds[3]:return
   entities.append({'id':f'raster-{len(entities)+1}','kind':kind,'class':cls,'bbox':bounds,'polygon':coords.tolist(),'coordinate_system':'original image pixels','original_dimensions':[w,h],'score':score,'method':'official junction/polygon reconstruction'})
  for p,typ in zip(polygons,types):
   cls=int(typ['class']);kind=typ['type']
   entity(p,ICONS[cls] if kind=='icon' else ROOMS[cls],kind)
  for poly,typ in zip(room_polygons,room_types):
   parts=list(poly.geoms) if hasattr(poly,'geoms') else [poly]
   for part in parts:
    if part.is_empty or not hasattr(part,'exterior'):continue
    entity(list(part.exterior.coords),ROOMS[int(typ['class'])],'room')
  post=time.perf_counter()-t
  # Save maps from real tensors for visual QA, not as instance-count substitutes.
  facts={'kind':'raster','entities':entities,'image_size':[w,h],'model':{'source':'https://github.com/CubiCasa/CubiCasa5k','revision':CUBI_REV,'weights_sha256':WEIGHT_SHA,'code_license':'CC BY-NC 4.0 per upstream LICENSE','weight_license':'upstream model; same project licence statement; verify before commercial use','training_overlap':'CubiCasa-trained; local source image overlap unknown, potentially trained-on','class_map':{'room':ROOMS,'icon':ICONS,'heatmap_channels':21}},'preprocessing':{'rgb':True,'normalization':'2*(RGB/255)-1','resize':'OpenCV INTER_LINEAR; aspect retained approximately, min side 128','original':[w,h],'processed':[pw,ph],'max_edge':self.max_edge,'padding':'none; upstream skip connections interpolate odd shapes','rotations':[list(pair) for pair in self.rotations],'interpolation_prediction':'bilinear align_corners=True; upstream split_prediction align_corners=False','postprocess_threshold':.2,'opening_classes':[1,2]},'timing':{'model_loading_seconds':load,'inference_seconds':inference,'postprocessing_seconds':post,'cold_model':cold},'peak_gpu_memory_bytes':peak,'warnings':['Experimental instance extraction; not completeness proof.','Bounded working resolution differs from original-size notebook inference.','No shower output channel; sauna bench is not a sauna room; bath is not specifically a separate WC room.','Double sink fixture counts depend on reconstructed icon boundaries; no bowl-level count is substituted.']}
  facts['_maps']=(raw_room.astype('uint8'),raw_icon.astype('uint8'))
  try:facts['words']=ocr_image(path) if self.ocr else []
  except Exception as e:facts['words']=[];facts['warnings'].append('OCR unavailable: '+str(e))
  return facts
