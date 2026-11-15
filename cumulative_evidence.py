"""Question-free local feature collection and bounded task-aware evidence packing.
No benchmark/reference imports. Native/learned outputs remain distinct hypotheses.
"""
import copy,json,hashlib,collections,time,os
from pathlib import Path
from qa.common import sha,write_json,inference_lock
from runtime_paths import CACHE_ROOT
VERSION='cumulative-evidence-v1'
def count_classes(rows):return dict(collections.Counter(e.get('class',e.get('kind','unknown'))for e in rows))
def custom_facts(file):
 from custom_detector import parse,model_info,SETTINGS
 import custom_detector
 info=model_info();key=hashlib.sha256(json.dumps([sha(file),info['weight_sha256'],sha(custom_detector.__file__),SETTINGS,VERSION],sort_keys=True).encode()).hexdigest();path=CACHE_ROOT/'cumulative-custom'/(key+'.json');started=time.perf_counter()
 if path.exists():
  r=json.loads(path.read_text());r['cache_hit']=True;r['execution']=dict(r.get('execution',{}),cache_hit=True);return r
 try:
  from demo_gpu import call
  with inference_lock():r=call(file,'custom_yolo',{})
 except Exception as e:
  r=parse(file,device='cpu');r['execution']=dict(r.get('execution',{}),fallback_reason=type(e).__name__+': host custom detector unavailable; CPU fallback')
 r['source_sha256']=sha(file);r['collection_seconds']=time.perf_counter()-started;write_json(path,r);return r

def augment(file,local,base_facts):
 """Extra detector runs once/document; caller saves immutable per-question projection."""
 outputs=[];evidence=[];suffix=Path(file).suffix.lower();base=base_facts.get('entities',[])
 native='pdf.native'if base_facts.get('kind')=='pdf'else'ifc.structured'if base_facts.get('kind')=='ifc'else'cubicasa'
 outputs.append({'model':native,'status':'available','counts':count_classes(base),'entities':len(base),'device':base_facts.get('device','cpu'),'cache_provenance':'shared document facts','warnings':base_facts.get('warnings',[])[:2]})
 # Preserve full underlying evidence outside the provider token budget.
 for e in base:
  e=copy.deepcopy(e);e['id']='base:'+str(e.get('id')or e.get('guid'));e['origin_model']=native;e['evidence_role']='native parsed fact'if native!='cubicasa'else'detector/reconstruction hypothesis';evidence.append(e)
 outputs.append({'model':'local.selected','status':local.get('status'),'answer':local.get('answer'),'unit':local.get('unit'),'route':local.get('route'),'evidence_ids':[e.get('id')for e in local.get('evidence',[])],'warnings':local.get('warnings',[])[:3]})
 for key,name in [('local_baseline','cubicasa.baseline'),('before_fixture_refinement','cubicasa.baseline'),('before_room_refinement','room.baseline'),('before_washing_refinement','washing.baseline'),('room_graph_alternative','room.graph')]:
  r=local.get(key)
  if isinstance(r,dict):outputs.append({'model':name,'status':r.get('status'),'answer':r.get('answer'),'unit':r.get('unit'),'evidence_count':len(r.get('evidence',[])),'note':'Alternative, never averaged or assumed comparable detector confidence'})
 if suffix=='.pdf':
  try:
   import pymupdf
   with pymupdf.open(file)as doc:
    if len(doc)!=1:raise ValueError('Custom visual PDF supplement currently limited to a single page; native multi-page scope retained')
    page=doc[0];scale=2048/max(page.rect.width,page.rect.height);render=CACHE_ROOT/'cumulative-pdf'/(sha(file)+'-page1-2048.png');render.parent.mkdir(exist_ok=True)
    if not render.exists():page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False).save(render)
    visual=custom_facts(render);outputs.append({'model':'custom_yolo','status':'available','counts':visual.get('counts',{}),'model_provenance':visual.get('model'),'cache_hit':visual.get('cache_hit',False),'execution':visual.get('execution'),'warning':'Whole rendered PDF page, possible legend objects; no completeness claim. Native evidence takes precedence for printed values.'})
    for e in visual['entities']:
     e=copy.deepcopy(e);e['id']='custom_yolo_pdf1:'+e['id'];e['bbox']=list(pymupdf.Rect(e['bbox'])*pymupdf.Matrix(1/scale,1/scale)*page.derotation_matrix);e.update(page=1,origin_model='custom_yolo',evidence_role='rendered PDF detector hypothesis',coordinate_system='PDF unrotated points');evidence.append(e)
  except Exception as exc:outputs.append({'model':'custom_yolo','status':'unavailable','reason':type(exc).__name__+': '+str(exc)[:120]})
 if suffix in['.png','.jpg','.jpeg']:
  try:
   from PIL import Image
   with Image.open(file)as im:
    if im.width*im.height>30_000_000:raise ValueError('Use original-resolution tile path for large sources; no global custom count asserted')
   from v2.structural import parse as structural_parse
   structural=structural_parse(file);outputs.append({'model':'rtdetr','status':'available','counts':count_classes(structural['entities']),'cache_hit':structural.get('cache_hit',False),'model_provenance':structural.get('model'),'execution':structural.get('execution')})
   for e in structural['entities']:e=copy.deepcopy(e);e['id']='rtdetr:'+e['id'];e['origin_model']='rtdetr';e['evidence_role']='structural detector hypothesis';evidence.append(e)
   try:
    from v2.ocr import parse as ocr_parse
    ocr=ocr_parse(file);outputs.append({'model':'ocr','status':'available','text_regions':len(ocr['words']),'cache_hit':ocr.get('cache_hit',False),'device':'cpu'})
    for e in ocr['words']:e=copy.deepcopy(e);e['id']='ocr:'+e['id'];e['origin_model']='ocr';e['evidence_role']='recognized text, not calibrated correctness';evidence.append(e)
   except Exception as exc:outputs.append({'model':'ocr','status':'unavailable','reason':type(exc).__name__})
   r=custom_facts(file);outputs.append({'model':'custom_yolo','status':'available','counts':r.get('counts',count_classes(r['entities'])),'question_counts':r.get('question_counts',{}),'model_provenance':r.get('model'),'settings':r.get('settings'),'cache_hit':r.get('cache_hit',False),'execution':r.get('execution'),'warning':'CubiCasa-trained; benches are not sauna rooms; source style and class semantics may differ.'})
   for e in r['entities']:e=copy.deepcopy(e);e['id']='custom_yolo:'+e['id'];e['origin_model']='custom_yolo';e['evidence_role']='detector hypothesis';evidence.append(e)
  except Exception as e:outputs.append({'model':'custom_yolo','status':'unavailable','reason':type(e).__name__+': '+str(e)[:140]})
 return {'version':VERSION,'outputs':outputs,'evidence':evidence,'source_sha256':sha(file),'note':'All relevant AVAILABLE local sources retained separately. This is not ground truth or a calibrated ensemble. No unrelated model is claimed to have run.'}

def compact_item(e):
 row={k:e[k]for k in ['id','guid','kind','class','name','label','room_number','area_m2','apartment','bbox','page','text','property','value','value_si','unit','origin_model','evidence_role','score','ocr_score']if k in e}
 if isinstance(row.get('text'),str)and len(row['text'])>240:row['text']=row['text'][:240]
 return row

def pack(local,facts,budget=7600):
 """Prioritize every selected local region, target-matched alternatives, native labels.
Reported omission counts prevent silent first-N truncation masquerading as completeness.
"""
 cumulative=local.get('cumulative_evidence',{});task=local.get('task',{});target=task.get('target');filters=task.get('filters',{});rows=[];seen=set();omitted=0
 sources=list(local.get('evidence',[]))+list(cumulative.get('evidence',[]))+list(facts.get('entities',[]))
 aliases={'window':{'window'},'door':{'door'},'toilet_fixture':{'toilet_fixture','toilet'},'sink':{'sink'},'shower_bath':{'shower','bathtub'},'sauna':{'sauna_bench','sauna'}}.get(target,{target})
 def priority(e):
  if e.get('id')in{r.get('id')for r in local.get('evidence',[])}:return 0
  if e.get('class')in aliases:return 1
  if filters.get('label_aliases')and str(e.get('label','')).casefold()in filters['label_aliases']:return 1
  return 2
 for e in sorted(sources,key=priority):
  id=e.get('id')or e.get('guid')
  if not id or id in seen:continue
  row=compact_item(e);row['id']=id
  if len(json.dumps(rows+[row],ensure_ascii=False).encode())>budget:omitted+=1;continue
  seen.add(id);rows.append(row)
 outputs=[]
 for o in cumulative.get('outputs',[]):
  outputs.append({k:o[k]for k in ['model','status','counts','question_counts','text_regions','answer','unit','route','warning','reason']if k in o})
 return rows,{'model_outputs':outputs,'provided_regions':len(rows),'omitted_regions':omitted,'complete_context':omitted==0,'limitations':cumulative.get('note','Available local evidence only; unavailable models were not run.')}

def decision(local,hybrid):
 """Presentation recommendation, not an accuracy oracle or confidence calibration."""
 status=hybrid.get('status')
 if status in['abstained','unsupported']:return {'selected':'abstained','reason':hybrid.get('explanation','Hybrid could not establish the requested answer.'),'recommended_review':True}
 if status!='success':return {'selected':'local','reason':'Hybrid did not return a valid answer; preserved Local is an unverified fallback.','recommended_review':True}
 agrees=hybrid.get('answer')==local.get('answer')and hybrid.get('unit')==local.get('unit')
 return {'selected':'hybrid','reason':'Hybrid proposal uses shared multi-source evidence. '+('Agreement is not independent proof.'if agrees else'Disagrees with Local; inspect cited source evidence.'),'recommended_review':not agrees,'agreement':agrees}
