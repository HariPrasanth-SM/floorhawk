"""Isolated campaign-only T4 extraction. No questions, references, presenter queue or API."""
import os,time,json,hashlib,base64,io,uuid
from pathlib import Path
import modal
from deploy.modal.app import image as base_image,weights
app=modal.App('floorhawk-campaign-extraction')
image=base_image.env({'PROOFPLAN_CACHE_ROOT':'/tmp/floorhawk-campaign-cache','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'})
SHA='95fd78b75b72f50963c03d710dbd38b9c7259e21e141c019f58ab7fbb57e54ea'
CLASSES=['electrical_appliance','door','bathtub','shower','window','sauna_bench','stairs','toilet','sink']
SETTINGS={'imgsz':1024,'conf':.05,'iou':.7,'max_det':500,'preprocessing':'Ultralytics YOLO letterbox; original pixel XYXY','version':'overnight-yolo-observations-v1'}
@app.cls(image=image,gpu='T4',cpu=2,memory=6144,timeout=180,max_containers=1,min_containers=0,scaledown_window=30,retries=0,volumes={'/weights':weights})
class Extractor:
 @modal.enter()
 def initialize(self):
  import torch
  from ultralytics import YOLO
  torch.set_num_threads(2);torch.cuda.set_per_process_memory_fraction(.60);self.worker=uuid.uuid4().hex;t=time.perf_counter();p=Path('/weights/campaign-assets-v1/floorplan_yolo11m.pt')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=SHA:raise ValueError('Custom weight SHA mismatch')
  self.model=YOLO(str(p));self.model.model.to('cuda:0');assert list(self.model.names.values())==CLASSES;self.loads=1;self.started=time.time();self.init_seconds=time.perf_counter()-t
 @modal.method()
 def extract(self,batch,deadline):
  import torch,psutil
  from PIL import Image,ImageOps
  if len(batch)>12 or sum(len(x['image_base64'])for x in batch)>32*1024**2:raise ValueError('Bounded batch exceeded')
  from campaign.clock import DEADLINES
  deadline=min(deadline,DEADLINES['optimize']);out=[]
  for row in batch:
   if set(row)!={'source_sha256','image_base64'}:raise ValueError('Only observation inputs allowed')
   if time.time()+8>deadline:break
   if psutil.virtual_memory().percent>72:raise RuntimeError('Cloud RAM admission pressure')
   raw=base64.b64decode(row['image_base64'],validate=True)
   if len(raw)>20*1024**2 or hashlib.sha256(raw).hexdigest()!=row['source_sha256']:raise ValueError('Source bound/hash mismatch')
   im=Image.open(io.BytesIO(raw))
   if im.width*im.height>30_000_000:out.append({'source_sha256':row['source_sha256'],'status':'unsupported','reason':'30MP campaign limit'});continue
   im=ImageOps.exif_transpose(im).convert('RGB');torch.cuda.reset_peak_memory_stats();t=time.perf_counter();devices=set();hook=self.model.model.register_forward_pre_hook(lambda m,args:devices.update(str(x.device)for x in args if isinstance(x,torch.Tensor)))
   try:r=self.model.predict(im,device=0,verbose=False,save=False,**{k:v for k,v in SETTINGS.items()if k in ['imgsz','conf','iou','max_det']})[0];torch.cuda.synchronize()
   finally:hook.remove()
   if 'cuda:0'not in devices:raise RuntimeError('No executing CUDA input tensor observed')
   out.append({'source_sha256':row['source_sha256'],'status':'success','image_size':[im.width,im.height],'model':{'name':'Supplied YOLO11m','weight_sha256':SHA,'classes':CLASSES},'settings':SETTINGS,'entities':[{'id':'custom-'+str(i+1),'class':{'toilet':'toilet_fixture','stairs':'stair'}.get(CLASSES[int(c)],CLASSES[int(c)]),'raw_class':CLASSES[int(c)],'score':float(s),'bbox':list(map(float,b)),'source_sha256':row['source_sha256'],'coordinate_system':'original raster pixels'}for i,(b,c,s)in enumerate(zip(r.boxes.xyxy.tolist(),r.boxes.cls.tolist(),r.boxes.conf.tolist()))],'execution':{'device':'cuda:0','tensor_devices':sorted(devices),'worker_id':self.worker,'loads':self.loads,'inference_seconds':time.perf_counter()-t,'initialization_seconds':self.init_seconds,'peak_gpu_memory_bytes':torch.cuda.max_memory_allocated(),'rss_bytes':psutil.Process().memory_info().rss,'gpu':'T4'}})
  return out
