from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Weakly count-supervised depicted-storey layout proposal model.
Produces real ink-region boxes; no minimum count, count lookup or hidden floors.
Layout regions can confuse separate apartments/insets with storeys: experimental.
"""
import json,math,hashlib,time
import numpy as np
from PIL import Image,ImageOps
from qa.common import ROOT,sha,write_json
FEATURE_VERSION='ink-layout-v1'
SETTINGS={'version':FEATURE_VERSION,'max_edge':1024,'gray_threshold':180,'kernels':[3,7,11,17],'min_box_area_fraction':.015,'min_ink_fraction':.002,'max_aspect':10,'max_regions':50}
MODEL=MODEL_ROOT/'v3-layout-model/calibration.json'
def proposals(file):
 import cv2
 source=sha(file);key=source+'-'+hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'v3-layout-proposals'/(key+'.json')
 if cache.exists():r=json.loads(cache.read_text());r['cache_hit']=True;return r
 started=time.perf_counter();im=ImageOps.exif_transpose(Image.open(file)).convert('RGB');w,h=im.size;factor=1024/max(w,h);scaled=im.resize((round(w*factor),round(h*factor)),Image.Resampling.LANCZOS);gray=cv2.cvtColor(np.asarray(scaled),cv2.COLOR_RGB2GRAY);ink=(gray<180).astype(np.uint8);ph,pw=ink.shape;result={}
 for kernel in SETTINGS['kernels']:
  mask=cv2.dilate(ink,np.ones((kernel,kernel),np.uint8));n,labels,stats,centers=cv2.connectedComponentsWithStats(mask,8);counts=np.bincount(labels[ink>0].ravel(),minlength=n);entities=[]
  for i in range(1,n):
   x,y,bw,bh,area=stats[i];ink_fraction=float(counts[i])/(pw*ph);box_fraction=float(bw*bh)/(pw*ph)
   if box_fraction<.015 or ink_fraction<.002 or max(bw/max(bh,1),bh/max(bw,1))>10:continue
   density=float(counts[i])/max(1,bw*bh);mn=min(bw/pw,bh/ph);mx=max(bw/pw,bh/ph);features=[1.,math.log(max(ink_fraction,1e-6)),math.log(box_fraction),math.log(max(density,1e-6)),abs(math.log(bw/bh)),mn,mx,(x+bw/2)/pw,(y+bh/2)/ph]
   entities.append({'id':f'layout-k{kernel}-{i}','class':'storey','bbox':[max(0,float(x)/factor),max(0,float(y)/factor),min(w,float(x+bw)/factor),min(h,float(y+bh)/factor)],'features':features,'ink_fraction':ink_fraction,'provenance':'Observed connected ink-region proposal; storey inclusion learned from drawing-level counts, no spatial ground truth'})
  result[str(kernel)]=sorted(entities,key=lambda e:e['ink_fraction'],reverse=True)[:50]
 r={'source_sha256':source,'image_size':[w,h],'settings':SETTINGS,'by_kernel':result,'timing_seconds':time.perf_counter()-started,'cache_hit':False};write_json(cache,r);return r

def predict(file):
 started=time.perf_counter();model=json.loads(MODEL.read_text())
 if model['feature_version']!=FEATURE_VERSION:raise ValueError('Layout feature version mismatch')
 if len(model['coefficients'])!=9 or not all(math.isfinite(x) for x in model['coefficients']):raise ValueError('Invalid layout checkpoint')
 loading=time.perf_counter()-started;features_started=time.perf_counter();r=proposals(file);features_seconds=time.perf_counter()-features_started;head_started=time.perf_counter();entities=[];discarded=[]
 for e in r['by_kernel'][str(model['kernel'])]:
  z=sum(a*b for a,b in zip(e['features'],model['coefficients']));score=1/(1+math.exp(-max(-40,min(40,z))));item={k:v for k,v in e.items() if k!='features'};item.update(score=score,weak_inclusion_score=score,included=score>=model['threshold'],source_sha256=r['source_sha256'],coordinate_system='original image pixels');(entities if item['included'] else discarded).append(item)
 return {'device':'cpu','status':'success','answer':len(entities),'unit':'count','evidence':entities,'route':'raster.weak-storey-layout.v3','model':{'name':'Count-supervised depicted-storey layout proposals','weight_sha256':sha(MODEL),'source_revision':sha(ROOT/'v3/layouts.py'),'training':'128 train-candidate drawing inputs; group-separated internal validation; weak counts, no spatial labels','class_map':{'0':'depicted storey layout hypothesis'},'license':'Derived from local company-provided CubiCasa-source drawings; preserve CC BY-NC-SA4.0 source restrictions; no commercial rights claim'},'layout_settings':dict(SETTINGS,kernel=model['kernel'],inclusion_threshold=model['threshold']),'layout_timing':{'model_loading_seconds':loading,'feature_seconds_this_call':features_seconds,'head_inference_seconds':time.perf_counter()-head_started,'total_seconds':time.perf_counter()-started,'feature_extraction_seconds_original':r['timing_seconds'],'cache_hit':r['cache_hit']},'layout_discarded':discarded,'warnings':['Experimental storey-layout hypotheses learned from drawing counts; separate apartments, legends or insets can be confused with levels.','Inclusion score is not calibrated probability. Zero does not verify absence. No hidden/building-wide levels are inferred.','Count accuracy does not prove localization; no compatible spatial annotations used.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in entities],'value':len(entities)}],'peak_gpu_memory_bytes':None}
