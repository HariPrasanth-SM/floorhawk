"""Opt-in large technical drawings: bounded source tiles, no global-head summation."""
import json,time,math,hashlib,re,copy,tempfile,io
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from qa.common import sha,write_json,inference_lock
from runtime_paths import CACHE_ROOT,RESULTS_ROOT
VERSION='source-tiles-v1';SETTINGS={'tile':1536,'overlap':.2,'detector_tiles':64,'ocr_tiles':12,'seconds':150,'ocr_seconds':90,'max_source_pixels':100_000_000}
def positions(length,tile=1536,overlap=.2):
 if length<=tile:return[0]
 out=list(range(0,length-tile+1,round(tile*(1-overlap))))
 if out[-1]!=length-tile:out.append(length-tile)
 return out
def overlap(a,b):
 w=max(0,min(a[2],b[2])-max(a[0],b[0]));h=max(0,min(a[3],b[3])-max(a[1],b[1]));i=w*h;aa=(a[2]-a[0])*(a[3]-a[1]);bb=(b[2]-b[0])*(b[3]-b[1]);return i/max(1,aa+bb-i),i/max(1,min(aa,bb))
def merge(items,text=False):
 out=[]
 for e in sorted(items,key=lambda e:-e.get('score',e.get('ocr_score',0))):
  same=lambda old:(re.sub(r'\W+','',old.get('text','').casefold())==re.sub(r'\W+','',e.get('text','').casefold()))if text else old.get('class')==e.get('class')
  if any(same(old)and(overlap(old['bbox'],e['bbox'])[0]>.45 or overlap(old['bbox'],e['bbox'])[1]>.75)for old in out):continue
  e=dict(e,id=('text-'if text else'instance-')+str(len(out)+1));out.append(e)
 return out
class LargeDrawing:
 def __init__(self,paired_engine=None):self.paired=paired_engine;self.root=CACHE_ROOT/'large-drawings';self.root.mkdir(exist_ok=True);self.images={}
 def extract(self,source,kind,progress=None):
  h=sha(source);key=hashlib.sha256(json.dumps([h,kind,SETTINGS,sha(__file__)]).encode()).hexdigest();folder=self.root/key;folder.mkdir(exist_ok=True);cache=folder/'facts.json'
  if cache.exists():
   saved=json.loads(cache.read_text());saved['live_execution']=[dict(e,cache_hit=True)for e in saved.get('live_execution',[])];return saved,True,folder
  from v2.supervisor import Admission,fresh_host
  if Admission().check(fresh_host())!='admit':raise RuntimeError('Resource admission paused; retry when the host worker is ready')
  started=time.perf_counter();entities=[];covered=[];events=[];errors=[]
  with Image.open(source)as raw:
   if raw.width*raw.height*12>900*1024**2:raise ValueError('Decoded image memory estimate exceeds900MiB; split this sheet before processing')
   if raw.width*raw.height>SETTINGS['max_source_pixels']:raise ValueError('Source pixel budget exceeded')
   image=ImageOps.exif_transpose(raw)if raw.getexif().get(274,1)!=1 else raw;w,hp=image.size;grid=[(x,y,min(x+1536,w),min(y+1536,hp))for y in positions(hp)for x in positions(w)]
   if kind=='ocr':
    # Fixed distributed source tiles, independent of answers; no blank-region rejection.
    anchors=[(.5,.1),(.65,.25),(.4,.45),(.7,.4),(.85,.75),(.25,.8),(.15,.2),(.4,.2),(.15,.5),(.5,.7),(.8,.1),(.5,.9)]
    selected=[]
    for ax,ay in anchors:
     b=min(grid,key=lambda b:((b[0]+b[2])/2-w*ax)**2+((b[1]+b[3])/2-hp*ay)**2)
     if b not in selected:selected.append(b)
    selected=selected[:SETTINGS['ocr_tiles']]
   else:selected=grid[:SETTINGS['detector_tiles']]
   for i,b in enumerate(selected):
    if time.perf_counter()-started>SETTINGS['ocr_seconds'if kind=='ocr'else'seconds']:break
    if Admission().check(fresh_host())!='admit':errors.append('Resource admission paused; partial coverage retained');break
    if progress:progress(f'Original-resolution {kind} tile {i+1}/{len(selected)}',i,len(selected))
    tile=folder/'active-tile.png';image.crop(b).convert('RGB').save(tile)
    try:
     from demo_gpu import _last
     _last.clear()
     if kind=='detector':
      from v2.structural import parse
      result=parse(tile);rows=result['entities']
     else:
      from v2.ocr import parse
      result=parse(tile);rows=result['words']
     for e in rows:
      e=copy.deepcopy(e);box=e.get('bbox')
      if box is None:continue
      e['bbox']=[box[0]+b[0],box[1]+b[1],box[2]+b[0],box[3]+b[1]];e.pop('polygon',None);e.update(page=1,tile=i+1,tile_source_bbox=list(b),coordinate_system='original_exif_normalized_pixels');entities.append(e)
     events.extend(copy.deepcopy(_last));covered.append({'tile':i+1,'bbox':list(b),'cache_hit':result.get('cache_hit',False),'timing':result.get('timing',{}),'device':result.get('execution',{}).get('device','cpu'if kind=='ocr'else'not recorded')})
    except Exception as exc:errors.append(type(exc).__name__+': '+str(exc)[:160]);break
   # The only disposable intermediate is task-owned active-tile.png.
   if (folder/'active-tile.png').exists():(folder/'active-tile.png').unlink()
  rows=merge(entities,kind=='ocr');full=len(covered)==len(grid);data={'kind':'raster','entities':rows,'source_sha256':sha(source),'image_size':[w,hp],'coverage':{'complete':full,'processed_tiles':len(covered),'full_grid_tiles':len(grid),'covered_regions':covered,'selection':'full-grid'if kind=='detector'else'fixed distributed12 source regions; incomplete OCR coverage'},'settings':SETTINGS,'warnings':errors+([]if full else['Partial source coverage; candidate instance count is not a sheet total. Text/crop selection is incomplete.']),'live_execution':events,'parse_seconds':time.perf_counter()-started,'extractor':kind,'version':VERSION};write_json(cache,data);return data,False,folder
 def answer(self,source,question,mode='local',on_local=None,progress=None):
  started=time.perf_counter();from qa.router import route
  task=route(question);is_count=task['operation']=='count';supported=is_count and task['target']in['window','door']and not task.get('filters');kind='detector'if supported else'ocr';facts,cached,folder=self.extract(source,kind,progress);evidence=facts['entities']
  if supported:evidence=[e for e in evidence if e.get('class')==task['target']]
  else:task={'operation':'property','target':'drawing_text','filters':{},'scope':'drawing','requested_unit':None}
  answer=None;status='abstained';trace=[]
  if supported and facts['coverage']['complete']:answer=len(evidence);status='success';trace=[{'operation':'count_unique_included_entities','entity_ids':[e['id']for e in evidence],'value':answer}]
  elif not is_count:
   # Return only literal OCR excerpts, not inferred dimensions/calibrations or inventories.
   pattern=r'pump|jockey|separator|strainer'if re.search(r'pump|equipment',question,re.I)else r'slab|reinforc|D1[036]|@'if re.search(r'slab|reinforc|thickness',question,re.I)else r'suction|header'if re.search(r'suction',question,re.I)else r'area|dorm|circulation|SF\b'
   excerpts=[e for e in evidence if re.search(pattern,e.get('text',''),re.I)]
   if excerpts:answer=[e['text']for e in excerpts[:15]];evidence=excerpts[:15];status='success'
  # One immutable document extraction; question-specific projection is separate.
  bundle=folder/'evidence.json'
  if not bundle.exists():write_json(bundle,{'source_sha256':facts['source_sha256'],'facts':facts,'warnings':facts['warnings'],'configuration':SETTINGS})
  result={'status':status,'answer':answer,'unit':'count'if supported else None,'task':task,'question':question,'source_sha256':facts['source_sha256'],'route':'large.source-tiles.'+kind,'model':{'name':'RT-DETR-L'if supported else'PP-OCRv5 CPU literal excerpts'},'evidence':evidence,'warnings':facts['warnings']+(['Global room/storey or scoped count aggregation is unsupported on tiles; no tile counts summed.']if is_count and not supported else[])+(['Literal OCR excerpts only; verify source context, not a complete inventory or interpreted specification.']if not supported else['Detector scores are not calibrated probabilities; completeness is not guaranteed by coverage.']),'calculation_trace':trace,'timing':{'total_seconds':time.perf_counter()-started,'cache_hit':cached},'shared_evidence':{'path':str(bundle),'sha256':sha(bundle),'key':folder.name},'coverage':facts['coverage'],'partial_candidate_count':len(evidence)if supported and not facts['coverage']['complete']else None,'coordinate_system':'original_exif_normalized_pixels','live_execution':facts['live_execution'],'device':next((e.get('device')for e in reversed(facts['live_execution'])if e.get('device')),'cpu'if kind=='ocr'else'not recorded')}
  # Overview plus up to3 source-resolution context tiles, selected by question words.
  media_path,frame=self.contact(source,question,evidence,facts,folder);result['provider_media']={'path':str(media_path),'frame':frame}
  if on_local:on_local(result)
  if mode=='hybrid'and self.paired:
   proposal=self.paired.hybrid(source,question,result)
   if supported and not facts['coverage']['complete']and proposal['status']=='success':proposal.update(status='abstained',answer=None,explanation='Partial detector coverage; a full-sheet total is not established.')
   result['paired']={'local':copy.deepcopy(result),'hybrid':proposal,'version':VERSION}
  return result
 def contact(self,source,question,evidence,facts,folder):
  key=hashlib.sha256(question.encode()).hexdigest();out=folder/('context-'+key+'.png');meta=folder/('context-'+key+'.json')
  if out.exists():return out,json.loads(meta.read_text())
  with Image.open(source)as raw:
   image=ImageOps.exif_transpose(raw)if raw.getexif().get(274,1)!=1 else raw;canvas=Image.new('RGB',(2048,2048),'white');overview=image.copy();overview.thumbnail((2048,950));canvas.paste(overview.convert('RGB'),(0,25));regions=[];words=set(re.findall(r'[a-z]{4,}',question.lower()))
   candidates=sorted(evidence,key=lambda e:-sum(w in e.get('text','').lower()for w in words));boxes=[]
   for e in candidates:
    b=e.get('tile_source_bbox',e['bbox'])
    if b not in boxes:boxes.append(b)
    if len(boxes)==3:break
   if not boxes:boxes=[r['bbox']for r in facts['coverage']['covered_regions'][:3]]
   for i,b in enumerate(boxes):
    crop=image.crop(b).convert('RGB');crop.thumbnail((1000,500));x=(i%2)*1024;y=1000+(i//2)*520;canvas.paste(crop,(x,y+20));ImageDraw.Draw(canvas).text((x,y),f'SOURCE CROP {i+1} {b}',fill='black');regions.append({'panel':i+1,'source_bbox':b,'mosaic_bbox':[x,y+20,x+crop.width,y+20+crop.height]})
   canvas.save(out)
  frame={'kind':'source_overview_and_crops','source_size':facts['image_size'],'crop_regions':regions,'coverage':facts['coverage']['selection'],'limitations':'Only3 readable context crops; overview is reduced; crop selection is incomplete, no calibrated raster scale.'};write_json(meta,frame);return out,frame
