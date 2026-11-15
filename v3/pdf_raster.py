from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Single-page PDF fallback through the existing local image model adapters.
Native evidence remains primary. Only explicit drawing counts with no unresolved
filters are supported; whole-model or multi-page quantities are never substituted.
"""
import json,copy,time
from qa.common import ROOT,sha,write_json
from .inventory import image_payload
SUPPORTED={'window','door','toilet_fixture','sink','bathtub'}
def render(file):
 import io,cv2,numpy as np
 from PIL import Image
 from qa.pipeline import Pipeline
 import pymupdf
 source=sha(file);dest=CACHE_ROOT/'v3-pdf-renders-crop';dest.mkdir(parents=True,exist_ok=True);image=dest/(source+'.png');meta=dest/(source+'.json')
 if image.exists() and meta.exists():r=json.loads(meta.read_text());return image,r
 facts,_,_,_=Pipeline().facts(file);anchors=[e for e in facts['entities'] if e.get('kind')=='room']
 if not anchors:
  from .pdf import parse as vector_parse
  anchors=vector_parse(file)['entities']
 if not anchors:raise ValueError('No native room anchors for excluding legends/title blocks safely')
 payload,frame,size=image_payload(file,max_edge=4096,max_bytes=None);whole=Image.open(io.BytesIO(payload)).convert('RGB');w,h=whole.size;rect=pymupdf.Rect(frame['rect']);rotation=pymupdf.Matrix(frame['derotation_matrix']);rotation.invert();boxes=[pymupdf.Rect(e['bbox'])*rotation for e in anchors if e.get('page',1)==1]
 if not boxes:raise ValueError('No page1 room anchors')
 x0=max(0,int(min(b.x0 for b in boxes)/rect.width*w));y0=max(0,int(min(b.y0 for b in boxes)/rect.height*h));x2=min(w,int(max(b.x1 for b in boxes)/rect.width*w)+1);y2=min(h,int(max(b.y1 for b in boxes)/rect.height*h)+1)
 ink=(cv2.cvtColor(np.asarray(whole),cv2.COLOR_RGB2GRAY)<170).astype(np.uint8);mask=cv2.dilate(ink,np.ones((3,3),np.uint8));n,labels,stats,_=cv2.connectedComponentsWithStats(mask,8);ids=set(np.unique(labels[y0:y2,x0:x2]).tolist())-{0};components=[stats[i] for i in ids if stats[i,4]>12 and stats[i,2]*stats[i,3]<.8*w*h]
 if components:
  bx0=min([x0]+[int(c[0]) for c in components]);by0=min([y0]+[int(c[1]) for c in components]);bx2=max([x2]+[int(c[0]+c[2]) for c in components]);by2=max([y2]+[int(c[1]+c[3]) for c in components]);padding=max(12,round(.02*max(bx2-bx0,by2-by0)))
 else:bx0,by0,bx2,by2=x0,y0,x2,y2;padding=max(32,round(.12*max(x2-x0,y2-y0)))
 crop=[max(0,bx0-padding),max(0,by0-padding),min(w,bx2+padding),min(h,by2+padding)]
 if crop[0]>=crop[2] or crop[1]>=crop[3]:raise ValueError('Invalid native-anchor crop')
 frame['display_crop_points']=[crop[0]/w*rect.width,crop[1]/h*rect.height,crop[2]/w*rect.width,crop[3]/h*rect.height];im=whole.crop(crop);im.thumbnail((2048,2048));im.save(image,format='PNG');r={'source_sha256':source,'rendered_sha256':sha(image),'frame':frame,'image_size':list(im.size),'whole_image_size':[w,h],'crop_pixels':crop,'native_room_anchors':len(anchors),'max_edge':2048,'version':'native-anchor-component-crop-v1','renderer':'4096px PyMuPDF RGB; native room anchors select connected ink components; page border/title/legend excluded before2048px model input'};write_json(meta,r);return image,r

def map_evidence(entities,metadata):
 import pymupdf
 frame=metadata['frame'];rect=pymupdf.Rect(frame['rect']);w,h=metadata['image_size'];crop=pymupdf.Rect(frame.get('display_crop_points',list(rect)));matrix=pymupdf.Matrix(crop.width/w,0,0,crop.height/h,crop.x0,crop.y0)*pymupdf.Matrix(frame['derotation_matrix']);result=[]
 for raw in entities:
  e=copy.deepcopy(raw);e['rendered_bbox']=e['bbox'];e['bbox']=list(pymupdf.Rect(e['bbox'])*matrix)
  if 'polygon' in e:e['rendered_polygon']=e['polygon'];e['polygon']=[list(pymupdf.Point(p)*matrix) for p in e['polygon']]
  if 'original_dimensions' in e:e['rendered_image_dimensions']=e.pop('original_dimensions')
  e.update(id='pdf-raster-'+e['id'],page=1,coordinate_system='PDF unrotated points',source_sha256=metadata['source_sha256'],rendered_source_sha256=metadata['rendered_sha256'],included=True);result.append(e)
 return result

def answer(file,task):
 if task.get('operation')!='count' or task.get('target') not in SUPPORTED or task.get('filters') or task.get('scope')!='drawing':return None
 started=time.perf_counter();image,meta=render(file)
 if task['target'] in ('window','door'):
  from v2.structural_tuned import answer as structural_answer
  raw=structural_answer(image,task)
 else:
  from .raster import parse
  from qa.tools import raster_answer
  facts=parse(image);raw=raster_answer(facts,task,'');raw.update(model=facts['model'],preprocessing=facts['preprocessing'],fixture_timing=dict(facts['timing'],cache_hit=facts['cache_hit'],parse_seconds=facts['parse_seconds']))
 if raw['status']!='success':return None
 entities=map_evidence(raw['evidence'],meta);result=dict(raw,answer=len(entities),evidence=entities,device='cpu',source_sha256=meta['source_sha256'],route='pdf.rendered-'+('rtdetr' if task['target'] in ('window','door') else 'cubicasa-fixture')+'.v3',pdf_rendering=meta,pdf_raster_seconds=time.perf_counter()-started,calculation_trace=[{'operation':'count_unique_included_entities','ids':[e['id'] for e in entities],'value':len(entities)}]);
 for field in ('raw_prediction','postprocessing','preprocessing'):
  if field in result:result['rendered_'+field]=result.pop(field)
 result['warnings']=raw.get('warnings',[])+['Experimental rendered-PDF image-model fallback; models trained mainly on CubiCasa plans, so Swiss/other drawing style is a domain shift.','Native PDF labels/schedules remain primary. Zero does not verify absence; check small symbols and missed objects.'];return result
