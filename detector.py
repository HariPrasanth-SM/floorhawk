from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Shared local inference adapter. No question files, expected counts or evaluation imports."""
import fcntl,hashlib,importlib.metadata,json,os,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ['YOLO_CONFIG_DIR']=str(CACHE_ROOT/'ultralytics')
os.environ['MPLCONFIGDIR']=str(CACHE_ROOT/'matplotlib')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def tile_origins(length,size,overlap):
 if length<=size:return [0]
 step=size-overlap
 if step<=0:raise ValueError('Tile overlap must be smaller than tile size')
 return sorted(set(list(range(0,length-size+1,step))+[length-size]))

def iou(a,b):
 x=max(0,min(a[2],b[2])-max(a[0],b[0]));y=max(0,min(a[3],b[3])-max(a[1],b[1]))
 inter=x*y;union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
 return inter/union if union>0 else 0

def map_box(local,origin,width,height):
 x,y=origin
 return [max(0,min(width,local[0]+x)),max(0,min(height,local[1]+y)),
         max(0,min(width,local[2]+x)),max(0,min(height,local[3]+y))]

def suppress(boxes,threshold):
 kept=[];removed=[]
 for b in sorted(boxes,key=lambda b:b['confidence'],reverse=True):
  duplicate=next((k for k in kept if k['class_id']==b['class_id'] and iou(k['xyxy'],b['xyxy'])>threshold),None)
  if duplicate:removed.append(b)
  else:kept.append(b)
 return kept,removed

def validate_boxes(boxes,width,height):
 import math
 if not isinstance(boxes,list) or len(boxes)>3000:raise ValueError('Expected at most 3000 boxes')
 clean=[]
 for b in boxes:
  coords=b.get('xyxy')
  if not isinstance(coords,list) or len(coords)!=4 or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in coords):raise ValueError('Each box needs four finite pixel coordinates')
  x1,y1,x2,y2=coords
  if not (0<=x1<x2<=width and 0<=y1<y2<=height):raise ValueError('Box must have positive area inside original image')
  clean.append({'xyxy':list(map(float,coords)),'included':b.get('included',True) is True,'class_name':'window','origin':'human_review','detector_score':b.get('detector_score')})
 return clean

def render(image,boxes,target,credit,title='Model predictions'):
 from PIL import Image,ImageDraw,ImageFont
 canvas=Image.open(image).convert('RGB');d=ImageDraw.Draw(canvas);font=ImageFont.load_default(size=max(12,min(22,canvas.width//70)))
 n=0
 for b in boxes:
  if not b.get('included',b.get('counted_as_window',True)):continue
  n+=1;coords=b['xyxy'];d.rectangle(coords,outline='#db451f',width=3)
  score=b.get('confidence',b.get('detector_score'));label=f'#{n}'+(f' score {score:.2f}' if score is not None else ' evidence')
  pos=(coords[0],max(0,coords[1]-22));d.rectangle(d.textbbox(pos,label,font=font),fill='white');d.text(pos,label,fill='#b83215',font=font)
 # Append attribution footer rather than covering source pixels. All box coordinates remain original.
 caption_font=ImageFont.load_default(size=12);lines=[];output_width=max(320,canvas.width)
 for text in [credit,f'{title}; included boxes: {n}. Detector scores are not probabilities.']:
  line=''
  for char in text:
   if d.textlength(line+char,font=caption_font)>output_width-10:
    lines.append(line);line=''
   line+=char
  lines.append(line)
 footer=Image.new('RGB',(output_width,canvas.height+12+18*len(lines)),'white');footer.paste(canvas,(0,0));d=ImageDraw.Draw(footer)
 for index,line in enumerate(lines):d.text((4,canvas.height+4+index*18),line,fill='black',font=caption_font)
 footer.save(target)

class Detector:
 def __init__(self,device='cpu'):
  if device not in ('cpu','0'):raise ValueError('Device must be cpu or 0')
  self.device=device;self.model=None;self.calls=0
 def predict(self,image,settings,credit='User-supplied drawing; attribution supplied by uploader',progress=None):
  from PIL import Image
  started=time.perf_counter();record={'status':'failed','device':self.device,'settings':settings.copy(),'peak_gpu_memory_bytes':None}
  (CACHE_ROOT).mkdir(exist_ok=True)
  with (CACHE_ROOT/'inference.lock').open('a') as lock:
   try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise RuntimeError('Another FloorHAWK inference is running. Wait for it to finish and retry.')
   try:
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(4);torch.manual_seed(0)
    if self.device=='0' and not torch.cuda.is_available():raise RuntimeError('CUDA is unavailable in this process. Restart with --device cpu or launch from your GPU-enabled terminal.')
    spec=json.loads((ROOT/'model.json').read_text());weights=ROOT/'weights'/spec['filename']
    if not weights.exists():raise RuntimeError('Checkpoint missing. Run proofplan/download_model.py.')
    if sha(weights)!=spec['sha256']:raise ValueError('Checkpoint SHA256 mismatch; download verified weights again.')
    cold=self.model is None;t=time.perf_counter()
    if cold:
     if progress:progress('Loading verified local model',0,1)
     self.model=YOLO(str(weights),task='detect')
     def capture_shape(module,args):
      if args and hasattr(args[0],'shape'):self.last_tensor_shape=list(args[0].shape)
     self.model.model.register_forward_pre_hook(capture_shape)
    record['model_loading_seconds']=time.perf_counter()-t if cold else 0.0
    names=[self.model.names[i] for i in range(len(self.model.names))]
    if names!=spec['class_names']:raise ValueError('Checkpoint class map mismatch')
    im=Image.open(image).convert('RGB');w,h=im.size
    size=settings.get('tile_size',0);overlap=settings.get('overlap',0)
    crops=[(x,y,min(x+size,w),min(y+size,h)) for y in tile_origins(h,size,overlap) for x in tile_origins(w,size,overlap)] if size else [(0,0,w,h)]
    if len(crops)>256:raise ValueError('Image requires over 256 tiles. Resize the drawing before upload.')
    if self.device=='0':torch.cuda.reset_peak_memory_stats(0);torch.cuda.synchronize()
    raw=[];transforms=[];t=time.perf_counter()
    for index,(x,y,x2,y2) in enumerate(crops):
     if progress:progress(f'Analyzing region {index+1} of {len(crops)}',index,len(crops))
     result=self.model.predict(source=im.crop((x,y,x2,y2)),conf=settings.get('candidate_conf',settings['conf']),iou=settings['iou'],imgsz=settings['imgsz'],device=self.device,max_det=1000,half=False,augment=False,save=False,verbose=False)[0]
     cw,ch=x2-x,y2-y
     if tuple(result.orig_shape)!=(ch,cw):raise ValueError('Unexpected crop coordinate dimensions')
     # Actual network tensor shape is recorded by a model forward pre-hook below when installed.
     transforms.append({'crop_xyxy':[x,y,x2,y2],'original_crop_size':[cw,ch],'result_orig_shape':list(result.orig_shape),'network_tensor_shape':getattr(self,'last_tensor_shape',None),'speed_ms':result.speed})
     for b in result.boxes.cpu():
      cls=int(b.cls.item());local=[float(v) for v in b.xyxy[0].tolist()];a,b0,c,d=local
      coords=map_box(local,(x,y),w,h)
      if coords[0]>=coords[2] or coords[1]>=coords[3]:continue
      border=(x>0 and a<3) or (y>0 and b0<3) or (x2<w and c>cw-3) or (y2<h and d>ch-3)
      raw.append({'class_id':cls,'class_name':names[cls],'confidence':float(b.conf.item()),'xyxy':coords,'local_xyxy':local,'tile_index':index,'internal_tile_border':bool(border)})
    if self.device=='0':torch.cuda.synchronize()
    record['inference_seconds']=time.perf_counter()-t
    t=time.perf_counter();kept,duplicates=suppress(raw,settings.get('cross_tile_iou',.45)) if size else (raw,[])
    counted=settings.get('count_classes',['window'])
    for b in kept:b['counted_as_window']=b['class_name'] in counted and b['confidence']>=settings['conf']
    windows=[dict(b,included=True,detector_score=b['confidence']) for b in kept if b['counted_as_window']]
    distributions={}
    for name in names:
     values=[b['confidence'] for b in raw if b['class_name']==name]
     distributions[name]={'n':len(values),'scores':sorted(values),'at_or_above_count_threshold':sum(v>=settings['conf'] for v in values)}
    record.update(status='success',model=spec,class_names=names,image_sha256=sha(image),image_size=[w,h],credit=credit,predicted_count=len(windows),boxes=windows,detections=kept,candidates=raw,duplicate_suppressed=duplicates,confidence_distributions=distributions,transforms=transforms,postprocessing_seconds=time.perf_counter()-t,cold_model=cold,cold_prediction=self.calls==0,coordinate_system='original decoded image pixels, xyxy, origin top-left',dependencies={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},source_revision='unversioned; SHA256 source snapshot',source_sha256={f:sha(ROOT/f) for f in ['detector.py','model.json','requirements.txt']},runtime_note='Inference includes PIL crop conversion, letterbox, model, per-region NMS; model loading and global merging recorded separately. GPU memory is PyTorch peak allocation, not device usage.')
    if self.device=='0':record['peak_gpu_memory_bytes']=torch.cuda.max_memory_allocated(0)
    self.calls+=1
   except Exception as exc:record.update(error=str(exc),traceback=traceback.format_exc())
   record['end_to_end_seconds']=time.perf_counter()-started
   return record
