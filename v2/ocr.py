from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""PP-OCRv5 mobile detector + Latin recognizer, ONNX CPU, local assets only.
Original image coordinates and raw strings are retained. No OCR accuracy claim
without transcripts; ambiguous room assignment abstains instead of duplicating.
"""
import hashlib,json,time,re,copy
from pathlib import Path
from qa.common import ROOT,sha,write_json,norm,inference_lock
from .supervisor import fresh_host,Admission
DIR=MODEL_ROOT/'ppocr-v5';_engine=None
SETTINGS={'version':'ppocr-latin-v1','engine':'ONNXRuntime CPU','det':'PP-OCRv5 mobile','rec':'PP-OCRv5 Latin mobile','classifier':'PP-OCRv2 mobile','det_side_limit':1280,'text_score':.5,'threads':2,'batch':1}

def engine():
 global _engine
 if _engine is None:
  provenance=json.loads((DIR/'provenance.json').read_text())
  for a in provenance['assets']:
   if sha((ROOT/a['path'])if(ROOT/a['path']).exists()else DIR/Path(a['path']).name)!=a['sha256']:raise RuntimeError('OCR asset hash mismatch')
  from rapidocr import RapidOCR,LangRec,OCRVersion
  _engine=RapidOCR(params={'Det.model_path':str(DIR/'ch_PP-OCRv5_mobile_det.onnx'),'Rec.model_path':str(DIR/'latin_PP-OCRv5_rec_mobile_infer.onnx'),'Cls.model_path':str(DIR/'ch_ppocr_mobile_v2.0_cls_infer.onnx'),'Det.ocr_version':OCRVersion.PPOCRV5,'Rec.ocr_version':OCRVersion.PPOCRV5,'Rec.lang_type':LangRec.LATIN,'Rec.rec_batch_num':1,'Cls.cls_batch_num':1,'Det.limit_side_len':1280,'Det.limit_type':'max','Global.max_side_len':1800,'Global.log_level':'warning','EngineConfig.onnxruntime.intra_op_num_threads':2,'EngineConfig.onnxruntime.inter_op_num_threads':1,'EngineConfig.onnxruntime.enable_cpu_mem_arena':False})
 return _engine

def parse(file):
 key=sha(file)+'-'+hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'v2-ocr'/(key+'.json');t=time.perf_counter()
 if cache.exists():r=json.loads(cache.read_text());r['cache_hit']=True;r['retrieval_seconds']=time.perf_counter()-t;return r
 if Admission().check(fresh_host())!='admit':raise RuntimeError('Resource admission paused')
 with inference_lock():
  cold=_engine is None;e=engine();load=time.perf_counter()-t;infer=time.perf_counter();output=e(str(file));words=[]
  for i,(poly,text,score) in enumerate(zip(output.boxes if output.boxes is not None else [],output.txts or [],output.scores or [])):
   coords=poly.tolist();xs=[p[0] for p in coords];ys=[p[1] for p in coords];words.append({'id':f'ppocr-{i+1}','text':text,'normalized':norm(text),'polygon':coords,'bbox':[min(xs),min(ys),max(xs),max(ys)],'ocr_score':float(score),'coordinate_system':'original image pixels','rotation':'quadrilateral; classifier0/180','method':'PP-OCRv5 Latin / RapidOCR3.4.1 ONNX CPU'})
  r={'source_sha256':sha(file),'words':words,'settings':SETTINGS,'asset_provenance':json.loads((DIR/'provenance.json').read_text()),'timing':{'loading_seconds':load,'inference_seconds':time.perf_counter()-infer,'total_seconds':time.perf_counter()-t,'cold_model':cold},'cache_hit':False};write_json(cache,r);return r

PATTERNS={'sauna':r'(?:s|sauna)','bedroom':r'(?:mh|makuuhuone|bedroom|schlafzimmer|chambre)','kitchen':r'(?:k|keittio|kitchen|kuche|cuisine|keittokomero)','wc_room':r'wc','bathroom':r'(?:kph|kh|ph|pesuhuone|bathroom|bad)','balcony':r'(?:parv\.?|parveke|balcony|balkon)'}

def associate(words,rooms,target):
 from shapely.geometry import Polygon,Point
 matched={};ambiguous=[]
 for w in words:
  if not re.fullmatch(PATTERNS[target],norm(w['text'])):continue
  b=w['bbox'];point=Point((b[0]+b[2])/2,(b[1]+b[3])/2);candidates=[]
  for room in rooms:
   poly=Polygon(room['polygon'])
   if poly.is_valid and poly.covers(point):candidates.append(room)
  if len(candidates)==1:matched.setdefault(candidates[0]['id'],{'room':candidates[0],'labels':[]})['labels'].append(w)
  elif len(candidates)>1:ambiguous.append(w['id'])
 return matched,ambiguous

def answer(file,task,facts):
 target=task.get('target')
 if task.get('operation')!='count' or target not in PATTERNS or task.get('filters'):return None
 r=parse(file);rooms=[e for e in facts['entities'] if e.get('kind')=='room' and e.get('class') not in ('background','outdoor')];matched,ambiguous=associate(r['words'],rooms,target)
 if ambiguous or not matched:return {'ocr_diagnostic':{'matched_rooms':len(matched),'ambiguous_labels':ambiguous,'timing':r['timing'],'cache_hit':r['cache_hit']}}
 selected=[]
 for item in matched.values():
  e=copy.deepcopy(item['room']);e['matched_labels']=item['labels'];e['provenance']='Unique OCR-label containment in reconstructed room polygon; no adjacency-only semantics';selected.append(e)
 return {'status':'success','answer':len(selected),'unit':'count','evidence':selected,'route':'raster.ppocr-room-association','ocr_timing':dict(r['timing'],cache_hit=r['cache_hit']),'warnings':['Label association counts only reconstructed rooms with recognized unique labels; omissions remain possible.','OCR score is a recognizer score, not calibrated correctness or completeness.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in selected]}]}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--output',required=True);a=p.parse_args();r=parse(a.image);write_json(a.output,r);print(json.dumps(r,ensure_ascii=False))
