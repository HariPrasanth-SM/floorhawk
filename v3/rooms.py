from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Learned fusion of native room semantics, fixture geometry and observed OCR.
Weak drawing-count supervision, mutually exclusive room-role hypotheses; no gold
at runtime, no fixed fallback counts, and no localization/completeness proof.
"""
import json,math,re,time,copy,hashlib
import numpy as np
from shapely.geometry import Polygon,Point
from qa.common import ROOT,sha,norm,inference_lock,write_json
from qa.raster import ROOMS
from v2.ocr import parse as ocr_parse
from .raster import parse
from .wash import candidates as geometry_candidates
ROLES=['bedroom','kitchen','bathroom','wc_room','sauna','balcony']
FEATURE_VERSION='semantic-geometry-ocr-room-fusion-v1'
MODEL=MODEL_ROOT/'v3-room-model/calibration.json'
PATTERNS={'bedroom':r'(?:mh|makuuhuone|bedroom|schlafzimmer|chambre)','kitchen':r'(?:k|kt|kk|keittio|keittiokomero|tupakeittio|kitchen|kuche|cuisine)','bathroom':r'(?:(?:kph|kh|ph|sh)(?:[ /+]+wc)?|pesuh\.?|pesuhuone|bathroom|bad)','wc_room':r'wc','sauna':r'(?:s|sauna)','balcony':r'(?:parv\.?|parveke|balcony|balkon)'}
NEGATIVE=r'(?:oh|olohuone|living room|et|eteinen|tk|tuulikaappi|vh|vaatehuone|var|varasto|storage|garage|autotalli)'
def features(file,facts,words):
 identity={'source':facts['source_sha256'],'feature_version':FEATURE_VERSION,'reference_settings':facts.get('settings',facts.get('preprocessing')),'observed_words_sha256':hashlib.sha256(json.dumps(words,sort_keys=True).encode()).hexdigest()};cache=CACHE_ROOT/'v3-room-features'/(hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()+'.json')
 if cache.exists():return json.loads(cache.read_text())['proposals']
 _,props=geometry_candidates(file,facts,room_classes=None)
 for e in props:
  native=e['segmentation_class'];poly=Polygon(e['polygon']);inside=[w for w in words if poly.covers(Point((w['bbox'][0]+w['bbox'][2])/2,(w['bbox'][1]+w['bbox'][3])/2))];flags=[]
  for role in ROLES:flags.append(float(any(re.fullmatch(PATTERNS[role],re.sub(r'\s*\d+$','',norm(w['text']))) for w in inside)))
  negative=float(any(re.fullmatch(NEGATIVE,re.sub(r'\s*\d+$','',norm(w['text']))) for w in inside));e['features']=e['features']+[float(native==c) for c in ROOMS]+flags+[negative];e['matched_labels']=[{'text':w['text'],'bbox':w['bbox'],'ocr_score':w.get('ocr_score')} for w in inside if any(re.fullmatch(PATTERNS[r],re.sub(r'\s*\d+$','',norm(w['text']))) for r in ROLES)];e['id']='room-fusion-'+e['id'];e['bbox_role']='reconstructed physical room polygon, weakly classified role';e.pop('class_name',None)
 write_json(cache,{'identity':identity,'proposals':props});return props

def predict(file,target):
 if target not in ROLES:raise ValueError('Unregistered room fusion target')
 started=time.perf_counter();model=json.loads(MODEL.read_text());loading=time.perf_counter()-started
 if model['feature_version']!=FEATURE_VERSION or model.get('roles')!=ROLES:raise ValueError('Room fusion feature version mismatch')
 if set(model.get('thresholds',{}))!=set(ROLES) or any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in model['thresholds'].values()):raise ValueError('Invalid room fusion thresholds')
 facts=parse(file);ocr=ocr_parse(file)
 with inference_lock():
  props=features(file,facts,ocr['words']);W=np.array(model['coefficients'],dtype=float)
  if W.shape!=(33,7) or not np.isfinite(W).all():raise ValueError('Invalid room fusion coefficients')
  X=np.array([p['features'] for p in props],dtype=float).reshape(-1,33);logits=X@W
  if len(props):logits-=logits.max(1,keepdims=True);scores=np.exp(logits);scores/=scores.sum(1,keepdims=True)
  else:scores=np.empty((0,7))
  selected=[];assignments=[]
  for e,s in zip(props,scores):
   role_index=int(s.argmax());role=ROLES[role_index-1] if role_index else 'none';score=float(s[role_index]);included=role!='none' and score>=model['thresholds'][role];assignments.append({'id':e['id'],'role':role,'weak_class_score':score,'included':included,'native_class':e['segmentation_class'],'bbox':e['bbox']})
   if role!=target or not included:continue
   e={k:v for k,v in e.items() if k!='features'};e.update(class_name=role,semantic_class=role,score=score,weak_class_score=score,included=True,source_sha256=facts['source_sha256'],coordinate_system='original image pixels',provenance='Learned room-role fusion over native semantic class, fixture geometry and observed OCR; trained with drawing-level counts only');e['class']=role;selected.append(e)
 return {'device':'cpu','status':'success','answer':len(selected),'unit':'count','evidence':selected,'route':'raster.weak-room-fusion.v3','model':{'name':'CubiCasa + PP-OCR count-supervised room fusion','weight_sha256':sha(MODEL),'base_weights_sha256':facts['model']['weights_sha256'],'source_revision':sha(ROOT/'v3/rooms.py'),'class_map':dict(enumerate(['none']+ROLES)),'supervision':'Drawing-level counts, group-separated validation; no spatial target labels','license':'Derived from company-provided CubiCasa-source training drawings; preserve source CC BY-NC-SA4.0 restrictions; no commercial rights claim'},'room_fusion_settings':{'feature_version':FEATURE_VERSION,'thresholds':model['thresholds'],'base_preprocessing':facts['preprocessing'],'ocr_settings':ocr['settings']},'room_assignments':assignments,'room_fusion_timing':{'model_loading_seconds':loading,'total_seconds':time.perf_counter()-started,'reference_parser_original':facts['timing'],'reference_parser_cache_hit':facts['cache_hit'],'ocr_original':ocr['timing'],'ocr_cache_hit':ocr['cache_hit']},'warnings':['Experimental room-role hypotheses learned from drawing counts; weak class scores are not calibrated probabilities.','Mutually exclusive roles are assigned to reconstructed room polygons; merged/missing regions and OCR errors remain possible.','Zero does not verify absence. Count agreement is not localization or completeness proof.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in selected],'value':len(selected)}],'peak_gpu_memory_bytes':None}

def native_label_answer(file,target):
 """Refine a native bedroom/kitchen class with contained labels, not partial counts."""
 if target not in ('bedroom','kitchen'):raise ValueError('Native-label refinement only supports bedroom/kitchen')
 started=time.perf_counter();facts=parse(file);ocr=ocr_parse(file)
 with inference_lock():
  props=features(file,facts,ocr['words']);selected=[];changes=[];j=ROLES.index(target)
  for p in props:
   f=p['features'];positive=bool(f[26+j]);other=any(f[26+i] for i in range(6) if i!=j) or bool(f[32]);native=p['segmentation_class']==target;included=positive or (native and not other)
   if included:
    e={k:v for k,v in p.items() if k!='features'};e.update(included=True,source_sha256=facts['source_sha256'],coordinate_system='original image pixels',provenance='Native room-class hypothesis refined by contained observed labels; OCR omissions are not treated as a complete competing count');e['class']=target;selected.append(e)
   if included!=native:changes.append({'id':p['id'],'native_class':p['segmentation_class'],'target_label_observed':positive,'other_label_observed':bool(other),'included':included})
 return {'device':'cpu','status':'success','answer':len(selected),'unit':'count','evidence':selected,'route':'raster.native-label-room-refinement.v3','model':{'name':'CubiCasa native room semantics + observed PP-OCR labels','weight_sha256':facts['model']['weights_sha256'],'source_revision':sha(ROOT/'v3/rooms.py'),'supervision':'Pretrained semantic class plus explicit observed-label refinement, no per-file count lookup','license':facts['model']['code_license']},'room_label_changes':changes,'room_fusion_timing':{'total_seconds':time.perf_counter()-started,'reference_parser_original':facts['timing'],'reference_parser_cache_hit':facts['cache_hit'],'ocr_original':ocr['timing'],'ocr_cache_hit':ocr['cache_hit']},'warnings':['Native semantics and OCR labels can both be wrong; observed labels refine individual regions rather than overwrite counts from a partial text inventory.','Merged/missing room polygons limit counting. Zero is not verified absence; no localization/completeness proof.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in selected],'value':len(selected)}],'device':'cpu','peak_gpu_memory_bytes':None}
