from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Weak count-supervised washing-installation region proposals.
Existing bathtub boxes plus a learned inclusion head on actual bath-room regions.
Room-sized support boxes are coarse localization hypotheses, not tight fixture proof.
"""
import json,math,copy
import numpy as np
from PIL import Image,ImageOps
from shapely.geometry import Polygon,Point
from qa.common import ROOT,sha,inference_lock
from .raster import parse
FEATURE_VERSION='wash-room-geometry-ink-v1'
MODEL=MODEL_ROOT/'v3-wash-model/calibration.json'
def candidates(file,facts,room_classes=('bath',)):
 im=np.asarray(ImageOps.exif_transpose(Image.open(file)).convert('L'));h,w=im.shape;icons=[e for e in facts['entities'] if e.get('kind')=='icon'];fixed=[dict(e) for e in icons if e['class']=='bathtub'];proposals=[]
 for room in facts['entities']:
  if room.get('kind')!='room' or (room_classes is not None and room.get('class') not in room_classes) or room.get('class') in ('background','wall','railing'):continue
  poly=Polygon(room['polygon'])
  if not poly.is_valid or poly.area<=0:continue
  b=room['bbox'];bw=max(b[2]-b[0],1);bh=max(b[3]-b[1],1);inside=[]
  for icon in icons:
   a=icon['bbox']
   if poly.covers(Point((a[0]+a[2])/2,(a[1]+a[3])/2)):inside.append(icon)
  counts={name:sum(i['class']==name for i in inside) for name in ('toilet_fixture','sink','bathtub','sauna_bench','electrical_appliance')};crop=im[max(0,int(b[1])):min(h,math.ceil(b[3])),max(0,int(b[0])):min(w,math.ceil(b[2]))]
  if crop.size==0:continue
  features=[1.,math.log(max(poly.area/(w*h),1e-6)),abs(math.log(bw/bh)),poly.area/(bw*bh),counts['toilet_fixture'],counts['sink'],counts['bathtub'],counts['sauna_bench'],counts['electrical_appliance'],float((crop<90).mean()),float((crop<180).mean()),float(crop.std()/255),min(bw/w,bh/h),max(bw/w,bh/h)]
  e=copy.deepcopy(room);e.update(id='wash-region-'+room['id'],segmentation_class=room['class'],class_name='washing installation hypothesis',bbox_role='coarse reconstructed bathing-room support region, not tight fixture localization',features=features,supporting_icon_ids=[i['id'] for i in inside]);e['class']='shower_bath';proposals.append(e)
 return fixed,proposals

def predict(file):
 model=json.loads(MODEL.read_text())
 if model['feature_version']!=FEATURE_VERSION or len(model['coefficients'])!=14 or not all(math.isfinite(x) for x in model['coefficients']):raise ValueError('Invalid washing-region calibration checkpoint')
 facts=parse(file)
 with inference_lock():
  fixed,proposals=candidates(file,facts);included=[dict(e,included=True,provenance='Existing CubiCasa bathtub instance prediction') for e in fixed];discarded=[]
  for e in proposals:
   z=sum(a*b for a,b in zip(e.pop('features'),model['coefficients']));score=1/(1+math.exp(-max(-40,min(40,z))));e.update(score=score,weak_inclusion_score=score,included=score>=model['threshold'],source_sha256=facts['source_sha256'],provenance='Learned count-supervised washing-installation hypothesis using room/fixture geometry and observed ink; no spatial target annotations')
   (included if e['included'] else discarded).append(e)
 return {'device':'cpu','status':'success','answer':len(included),'unit':'count','evidence':included,'route':'raster.weak-washing-regions.v3','model':{'name':'Count-supervised washing-installation region head + CubiCasa bathtub instances','weight_sha256':sha(MODEL),'source_revision':sha(ROOT/'v3/wash.py'),'base_weights_sha256':facts['model']['weights_sha256'],'class_map':{'0':'bathtub instance','1':'additional shower/bath installation hypothesis'},'supervision':'Drawing-level counts only; coarse room proposal boxes, no spatial labels','license':'Company-provided CubiCasa-source training drawings; preserve source CC BY-NC-SA4.0 restrictions; no commercial rights claim'},'wash_settings':{'feature_version':FEATURE_VERSION,'inclusion_threshold':model['threshold'],'base_preprocessing':facts['preprocessing']},'wash_discarded':discarded,'fixture_timing':dict(facts['timing'],cache_hit=facts['cache_hit'],parse_seconds=facts['parse_seconds']),'warnings':['Experimental weakly supervised installation counts. Some boxes cover a whole bathing room as support, not the exact fixture extent.','At most one learned additional installation per reconstructed bath region; multiple showers in one room can be missed.','A bath region is not automatically counted: the learned head selects proposals. Inclusion scores are not calibrated probabilities. Zero does not verify absence.','Count agreement does not establish localization; compatible spatial annotations were unavailable.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in included],'value':len(included)}],'peak_gpu_memory_bytes':None}
