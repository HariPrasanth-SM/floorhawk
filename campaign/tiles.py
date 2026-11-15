"""Isolated original-resolution RT-DETR tiles, bounded source coverage and real boxes."""
import os,json,time,hashlib,math,argparse
from pathlib import Path
from PIL import Image,ImageOps
from qa.common import sha,inference_lock
from runtime_paths import DATASET_ROOT,MODEL_ROOT
from .clock import atomic,admit,now
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115';SETTINGS={'version':'campaign-source-tiles-v1','source_tile':1024,'overlap':.2,'imgsz':1024,'conf':.25,'iou':.5,'max_det':300,'max_tiles':16,'seconds':100,'padding':'white source tiles; no content-based blank filtering','mapping':'model source tile pixels + tile origin, clamped to source extent'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=60);a=p.parse_args();import torch
 torch.set_num_threads(2)
 from ultralytics import RTDETR
 from v2.structural import SHA256,CLASSES
 weight=MODEL_ROOT/'rtdetr/rtdetr_l_autoresearch_60ep.pt';assert sha(weight)==SHA256;t=time.monotonic();net=RTDETR(str(weight));net.model.to('cpu');loading=time.monotonic()-t
 rows=json.loads((OUT/'observations/manifest.json').read_text())['sources'];rows=sorted(rows,key=lambda r:hashlib.sha256(('tiles-dev-v1'+r['source_sha256']).encode()).hexdigest())[:a.n];folder=OUT/'observations/rtdetr-tiles';folder.mkdir(exist_ok=True);atomic(OUT/'tile-selection.json',{'time':now(),'source_only_selection':True,'sources':rows,'settings':SETTINGS,'weight_sha256':SHA256})
 for row in rows:
  admit('optimize',120);key=hashlib.sha256(json.dumps([row['source_sha256'],SHA256,SETTINGS],sort_keys=True).encode()).hexdigest();dest=folder/(key+'.json')
  if dest.exists():continue
  file=DATASET_ROOT/row['path'];im=Image.open(file)
  if im.width*im.height>30_000_000:atomic(dest,dict(row,status='unsupported',reason='Isolated30MP bound'));continue
  im=ImageOps.exif_transpose(im).convert('RGB');w,h=im.size;edge=1024;step=819;tiles=[(x,y,min(x+edge,w),min(y+edge,h))for y in range(0,max(1,h-205),step)for x in range(0,max(1,w-205),step)];entities=[];covered=[];start=time.monotonic()
  for i,b in enumerate(tiles):
   if i>=16 or time.monotonic()-start>100:break
   admit('optimize',15);tile=Image.new('RGB',(edge,edge),'white');tile.paste(im.crop(b),(0,0));t=time.monotonic()
   with inference_lock():r=net.predict(tile,conf=.25,iou=.5,imgsz=1024,max_det=300,device='cpu',verbose=False,save=False)[0]
   for j,(box,c,s)in enumerate(zip(r.boxes.xyxy.tolist(),r.boxes.cls.tolist(),r.boxes.conf.tolist())):
    x1,y1,x2,y2=box;box=[max(b[0],x1+b[0]),max(b[1],y1+b[1]),min(b[2],x2+b[0]),min(b[3],y2+b[1])]
    if box[0]>=box[2]or box[1]>=box[3]:continue
    entities.append({'id':f'tile-{i+1}-{j+1}','class':CLASSES[int(c)],'bbox':box,'score':float(s),'source_sha256':row['source_sha256'],'tile':i+1,'tile_region':b,'internal_border_fragment':(x1<5 and b[0]>0)or(y1<5 and b[1]>0)or(x2>1019 and b[2]<w)or(y2>1019 and b[3]<h),'coordinate_system':'original source pixels'})
   covered.append(list(b))
  atomic(dest,{'status':'success'if len(covered)==len(tiles)else'partial','source_sha256':row['source_sha256'],'path':row['path'],'image_size':[w,h],'entities':entities,'coverage':{'complete':len(covered)==len(tiles),'tiles_total':len(tiles),'tiles_completed':len(covered),'covered_regions':covered},'settings':SETTINGS,'model':{'name':'RT-DETR-L','weight_sha256':SHA256},'execution':{'device':'cpu','model_device':str(next(net.model.parameters()).device),'inference_seconds':time.monotonic()-start,'model_loading_seconds':loading,'peak_gpu_memory_bytes':None},'cache_key':key});print(row['path'],len(covered),len(entities),round(time.monotonic()-start,2),flush=True)
if __name__=='__main__':main()
