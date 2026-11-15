from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Native labelled vector-room extraction supplement; no associated IFC lookup.
Only unique label/number pairs with unambiguous non-gray filled polygons and
explicit physical scale can yield areas. Inconsistent overlapping labels abstain.
"""
import json,re,time,hashlib,math
from qa.common import ROOT,sha,write_json,norm
from qa.tools import success,unsupported,count
VERSION='vector-labelled-rooms-v2'
def parse(file):
 import pymupdf
 from shapely.geometry import Polygon,Point
 h=sha(file);key=h+'-'+VERSION;cache=CACHE_ROOT/'v3-pdf'/(key+'.json')
 if cache.exists():r=json.loads(cache.read_text());r['cache_hit']=True;return r
 started=time.perf_counter();entities=[];diagnostics=[]
 with pymupdf.open(file) as doc:
  page_count=len(doc)
  for pn,page in enumerate(doc):
   scales={int(v) for v in re.findall(r'1\s*:\s*(\d+)',page.get_text())};ratio=next(iter(scales)) if len(scales)==1 else None;polys=[]
   for drawing in page.get_drawings():
    fill=drawing.get('fill');items=drawing['items']
    if not fill or max(fill)-min(fill)<.03:continue
    if all(i[0]=='l' for i in items) and len(items)>=3:
     pts=[tuple(items[0][1])]+[tuple(i[2]) for i in items]
     if math.dist(pts[0],pts[-1])>1:continue
     poly=Polygon(pts)
     if poly.is_valid and 10<poly.area<page.rect.width*page.rect.height*.8:polys.append(poly)
   lines=[]
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     text=''.join(s['text'] for s in line['spans']).strip()
     if text:lines.append({'text':text,'bbox':list(line['bbox'])})
   for label in lines:
    if not re.fullmatch(r'[\wÀ-ÿ][\wÀ-ÿ .\-/]{1,45}',label['text']) or not any(c.isalpha() for c in label['text']):continue
    b=label['bbox'];x=(b[0]+b[2])/2
    ids=[l for l in lines if re.fullmatch(r'\d{1,3}',l['text']) and -.5*(b[3]-b[1])<=l['bbox'][1]-b[3]<=max(12,2*(b[3]-b[1])) and abs((l['bbox'][0]+l['bbox'][2])/2-x)<8]
    if len(ids)!=1:continue
    ident=ids[0];point=Point(x,(b[1]+ident['bbox'][3])/2);containing=[p for p in polys if p.covers(point)]
    # Multiple overlapping nonidentical space shapes are ambiguous, not an area pick.
    unique=[]
    for poly in containing:
     if not any(poly.symmetric_difference(old).area/max(poly.area,old.area)<.001 for old in unique):unique.append(poly)
    poly=unique[0] if len(unique)==1 else None
    area=poly.area*(ratio*.0254/72)**2 if poly is not None and ratio else None
    entities.append({'id':f'vector-{pn+1}-{len(entities)+1}','kind':'room','class':'labelled_room','label':label['text'],'room_number':ident['text'],'bbox':[min(b[0],ident['bbox'][0]),b[1],max(b[2],ident['bbox'][2]),ident['bbox'][3]],'page':pn+1,'area_m2':area,'area_method':'unique native filled space polygon at explicit physical PDF scale' if area is not None else 'ambiguous/missing native space boundary or scale','polygon':list(poly.exterior.coords) if poly is not None else None,'coordinate_system':'PDF unrotated points','source_sha256':h,'included':True})
   diagnostics.append({'page':pn+1,'scale':ratio,'non_gray_space_shapes':len(polys)})
 result={'entities':entities,'pages':page_count,'diagnostics':diagnostics,'version':VERSION,'cache_hit':False,'timing_seconds':time.perf_counter()-started};write_json(cache,result);return result

def answer(file,task):
 if task.get('scope')=='model' or task.get('target')!='room' or task.get('operation') not in ('count','area'):return None
 f=task.get('filters',{})
 if set(f)-{'label','room_number','quantity_kind','indoor_only','page'}:return None
 r=parse(file)
 if r['pages']>1 and not f.get('page'):return None
 selected=[e for e in r['entities'] if (not f.get('page') or e['page']==f['page']) and (not f.get('label') or norm(e['label'])==norm(f['label'])) and (not f.get('room_number') or e['room_number']==str(f['room_number']))]
 if not selected:return None
 # Different labels at the same location imply overlaid source variants.
 ambiguous=[e for e in selected if any(e['page']==o['page'] and norm(e['label'])!=norm(o['label']) and abs((e['bbox'][0]+e['bbox'][2]-o['bbox'][0]-o['bbox'][2])/2)<4 and abs(e['bbox'][1]-o['bbox'][1])<4 for o in r['entities'])]
 if ambiguous:return None
 if task['operation']=='count':result=count(selected,'Unique native labelled room instances; overlaid-label ambiguity rejected')
 else:
  if any(e['area_m2'] is None for e in selected):return None
  if f.get('room_number') and len(selected)!=1:return None
  result=success(round(sum(e['area_m2'] for e in selected),6),'m2',selected,[{'operation':'sum_evidenced_room_areas','terms':[{'entity_id':e['id'],'value':e['area_m2'],'unit':'m2'} for e in selected]}],['Area derives from native vector space boundary and explicit printed scale; original PDF physical size is assumed.'])
 result.update(route='pdf.native-vector-rooms.v3',vector_pdf_version=VERSION,vector_pdf_timing_seconds=r['timing_seconds']);return result
