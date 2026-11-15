"""Small source-evidence proposal selector. Pure JSON inference; never sees gold/IDs."""
import math,re,copy,json
from qa.common import norm
from v3.dedup import overlap
VERSION='grounded-proposal-selector-v1'
TARGETS=['door','window','bedroom','kitchen','bathroom','wc_room','sauna','balcony','storey']
PATTERNS={'bedroom':r'(?:mh|makuuhuone|bedroom|schlafzimmer|chambre)','kitchen':r'(?:k|kt|kk|keittio|keittiokomero|tupakeittio|kitchen|kuche|cuisine)','bathroom':r'(?:kph|kh|ph|sh|pesuh\.?|pesuhuone|bathroom|bad)(?:[ /+]+wc)?','wc_room':r'wc','sauna':r'(?:s|sauna)','balcony':r'(?:parv\.?|parveke|balcony|balkon)'}
def label_regions(words,target):
 if target not in PATTERNS:return []
 kept=[]
 for w in words:
  text=re.sub(r'\s*\d+(?:[.,]\d+)?\s*(?:m2|m²)?$','',norm(w['text'])).strip()
  if w.get('ocr_score',0)<.5 or not re.fullmatch(PATTERNS[target],text):continue
  e=dict(w,id='label:'+w['id'],class_name=target,**{'class':target},origin_model='PP-OCRv5',provenance='Observed printed room label; text region, not invented room boundary')
  if not any(overlap(e['bbox'],k['bbox'])[0]>.5 for k in kept):kept.append(e)
 return kept

def proposals(local,review,words):
 candidates=[]
 if local.get('status')=='success'and type(local.get('answer'))in[int,float]:candidates.append(('local',local))
 target=local.get('task',{}).get('target')
 if review and target in review.get('requested',[])and target not in review.get('uncertain',[]):
  entities=[{k:v for k,v in e.items()if k!='score'}for e in review.get('entities',[])if e['class']==target];r=copy.deepcopy(local);r.update(status='success',answer=len(entities),unit='count',evidence=entities,route='gemini.grounded-scene-review',model={'name':review['model']},review_observation={'version':review['version'],'prompt_sha256':review['prompt_sha256'],'model':review['model'],'generation_seconds':review['generation_seconds'],'usage':review['usage']});candidates.append(('review',r))
 if target in PATTERNS:
  regions=label_regions(words,target)
  if regions:
   r=copy.deepcopy(local);r.update(status='success',answer=len(regions),unit='count',evidence=regions,route='raster.explicit-ocr-labels.campaign-v1',warnings=list(local.get('warnings',[]))+['Count follows observed room-label instances. OCR omissions and duplicate room labels remain possible; no completeness guarantee.']);candidates.append(('ocr',r))
 return candidates

def features(local,candidate,origin,review,words,image_size):
 target=local.get('task',{}).get('target');value=float(candidate['answer']);base=float(local.get('answer')or 0);w,h=image_size;boxes=[e['bbox']for e in candidate.get('evidence',[])if e.get('bbox')];areas=[max(0,(b[2]-b[0])*(b[3]-b[1]))/max(1,w*h)for b in boxes];scores=[e.get('score')for e in candidate.get('evidence',[])if isinstance(e.get('score'),(int,float))];labels=label_regions(words,target);label_n=len(labels);review_n=len([e for e in(review or{}).get('entities',[])if e['class']==target]);all_rooms=len([e for e in(review or{}).get('entities',[])if e['class']in PATTERNS]);s=sum(scores)/len(scores)if scores else 0;matched=0
 for b in boxes:
  if any(b[0]<=(e['bbox'][0]+e['bbox'][2])/2<=b[2]and b[1]<=(e['bbox'][1]+e['bbox'][3])/2<=b[3]for e in labels):matched+=1
 log=lambda x:math.log1p(max(0,x))
 return [float(target==t)for t in TARGETS]+[float(origin==s)for s in ['local','review','ocr']]+[log(value),float(value==0),log(base),log(review_n),log(label_n),value-base,value-review_n,value-label_n,float(value==base),float(value==review_n),float(value==label_n),len(boxes)/max(1,value),sum(areas),sum(areas)/len(areas)if areas else 0,max(areas,default=0),s,min(scores,default=0),matched/max(1,len(boxes)),log(len(words)),float(bool(words)),math.log(max(w,1)/max(h,1)),log(w*h),log(all_rooms),float(target in(review or{}).get('uncertain',[]))]
FEATURE_NAMES=['target:'+t for t in TARGETS]+['proposal:'+s for s in ['local','review','ocr']]+['log_count','is_zero','log_local_count','log_review_count','log_observed_label_count','difference_local','difference_review','difference_labels','equals_local','equals_review','equals_labels','regions_per_instance','total_box_fraction','mean_box_fraction','maximum_box_fraction','mean_detector_score','minimum_detector_score','matched_label_fraction','log_ocr_words','ocr_available','log_aspect','log_pixels','log_review_rooms','review_uncertain']
def tree_value(tree,x):
 if 'leaf'in tree:return tree['leaf']
 return tree_value(tree['left']if x[tree['feature']]<=tree['threshold']else tree['right'],x)
def rank(model,x):
 z=model['intercept']+model['learning_rate']*sum(tree_value(t,x)for t in model['trees']);return 1/(1+math.exp(-max(-35,min(35,z))))
def select(local,review,words,image_size,model):
 if model['version']!=VERSION or model['features']!=FEATURE_NAMES:raise ValueError('Selector feature contract mismatch')
 candidates=proposals(local,review,words)
 if not candidates:return copy.deepcopy(local)
 ranked=[(rank(model,features(local,r,origin,review,words,image_size)),origin,r)for origin,r in candidates];score,origin,result=max(ranked,key=lambda p:(p[0],p[1]=='local'));result=copy.deepcopy(result);result['selector']={'version':VERSION,'selected':origin,'score_is_not_probability':True,'alternatives':[{'source':o,'answer':r['answer'],'selection_score':s}for s,o,r in ranked],'reason':'Group-validated evidence-feature selector among existing local/review/explicit-label proposals; no count averaging'};return result
