from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Local four-crop OCR, coordinate-restored and text/box-deduplicated.
No question or reference answers enter image extraction.
"""
import hashlib,json,time,copy,re
from PIL import Image,ImageOps
import numpy as np
from qa.common import ROOT,sha,write_json,inference_lock,norm
from v2.ocr import engine,parse as original_parse,PATTERNS,associate
from v2.supervisor import Admission,fresh_host
from .dedup import overlap
SETTINGS={'version':'four-crop-2x-v1','grid':2,'overlap_fraction':.2,'upscale':2,'max_crop_edge':1600,'score':.5}
def parse(file):
 h=sha(file);key=h+'-'+hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'v3-ocr'/(key+'.json');t=time.perf_counter()
 if cache.exists():r=json.loads(cache.read_text());r['cache_hit']=True;return r
 if Admission().check(fresh_host())!='admit':raise RuntimeError('Resource admission paused')
 raw=original_parse(file);words=copy.deepcopy(raw['words']);im=ImageOps.exif_transpose(Image.open(file)).convert('RGB');w,hgt=im.size;crops=[]
 with inference_lock():
  e=engine()
  for ix in range(2):
   for iy in range(2):
    x0=0 if ix==0 else int(w*.4);y0=0 if iy==0 else int(hgt*.4);x2=int(w*.6) if ix==0 else w;y2=int(hgt*.6) if iy==0 else hgt
    crop=im.crop((x0,y0,x2,y2));factor=min(2,1600/max(crop.size));crop=crop.resize((round(crop.width*factor),round(crop.height*factor)),Image.Resampling.LANCZOS);s=time.perf_counter();out=e(np.asarray(crop));crops.append({'bbox':[x0,y0,x2,y2],'scale':factor,'seconds':time.perf_counter()-s})
    for poly,text,score in zip(out.boxes if out.boxes is not None else [],out.txts or [],out.scores or []):
     poly=poly.astype(float);poly[:,0]=poly[:,0]/factor+x0;poly[:,1]=poly[:,1]/factor+y0;box=[float(poly[:,0].min()),float(poly[:,1].min()),float(poly[:,0].max()),float(poly[:,1].max())]
     duplicate=next((old for old in words if norm(old['text'])==norm(text) and overlap(old['bbox'],box)[1]>.5),None)
     if duplicate:continue
     words.append({'id':'cropocr-'+str(len(words)+1),'text':text,'normalized':norm(text),'bbox':box,'polygon':poly.tolist(),'ocr_score':float(score),'coordinate_system':'original image pixels','method':'PP-OCRv5 Latin four overlapping crops 2x'})
 r={'source_sha256':h,'words':words,'settings':SETTINGS,'crops':crops,'timing':{'inference_seconds':sum(c['seconds'] for c in crops),'total_seconds':time.perf_counter()-t},'cache_hit':False};write_json(cache,r);return r

def candidates(file,facts):
 raw=parse(file);rooms=[e for e in facts['entities'] if e.get('kind')=='room' and e.get('class')!='background'];results={}
 # Expanded abbreviations come from documented Finnish plan conventions, not answers.
 patterns=dict(PATTERNS,kitchen=r'(?:k|kt|kk|keittio|keittiokomero|tupakeittio|kitchen|kuche|cuisine)',bathroom=r'(?:(?:kph|kh|ph|sh)(?:[ /+]+wc)?|pesuh\.?|pesuhuone|bathroom|bad)',balcony=r'(?:parv\.?|parveke|lasitettu parveke|balcony|balkon)')
 for target,pattern in patterns.items():
  words=[dict(w,text=re.sub(r'\s*\d+$','',w['text'])) for w in raw['words'] if re.fullmatch(pattern,re.sub(r'\s*\d+$','',norm(w['text'])))];matched,ambiguous=associate_for_pattern(words,[r for r in rooms if target=='balcony' or r.get('class')!='outdoor'])
  results[target]={'entities':[dict(item['room'],matched_labels=item['labels']) for item in matched.values()],'ambiguous':ambiguous,'matched_label_count':len(words)}
 return {'results':results,'ocr':raw}
def associate_for_pattern(words,rooms):
 from shapely.geometry import Polygon,Point
 matched={};ambiguous=[]
 for word in words:
  b=word['bbox'];p=Point((b[0]+b[2])/2,(b[1]+b[3])/2);candidates=[r for r in rooms if Polygon(r['polygon']).is_valid and Polygon(r['polygon']).covers(p)]
  if len(candidates)==1:matched.setdefault(candidates[0]['id'],{'room':candidates[0],'labels':[]})['labels'].append(word)
  elif len(candidates)>1:ambiguous.append(word['id'])
 return matched,ambiguous
