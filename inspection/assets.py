from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Inference-free source previews/crops. No reference/evaluator/provider imports."""
import io,json,hashlib,math,re,threading,xml.etree.ElementTree as ET,time
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from qa.common import ROOT,sha,write_json
CACHE=CACHE_ROOT/'inspection-assets';CACHE.mkdir(exist_ok=True);LOCK=threading.RLock();MAX_PIXELS=4_000_000;MAX_CACHE_BYTES=256*1024**2

def safe_svg(raw):
 if len(raw)>20*1024**2 or re.search(br'<!\s*(?:DOCTYPE|ENTITY)',raw,re.I):raise ValueError('Unsafe SVG declarations/size')
 root=ET.fromstring(raw)
 if root.tag.split('}')[-1]!='svg':raise ValueError('Not SVG')
 allowed={'svg','g','defs','path','rect','circle','ellipse','line','polyline','polygon','text','tspan','title','desc','linearGradient','radialGradient','stop','clipPath','mask','symbol','use'}
 def clean(node):
  for child in list(node):
   if child.tag.split('}')[-1]not in allowed:node.remove(child)
   else:clean(child)
  for k,v in list(node.attrib.items()):
   name=k.split('}')[-1].lower();bad=name.startswith('on')or name in ['src','base']or('href'in name and not v.startswith('#'))or re.search(r'javascript:|@import|expression\s*\(',v,re.I)or any(not x.strip(' \"\'').startswith('#')for x in re.findall(r'url\((.*?)\)',v,re.I))
   if bad:del node.attrib[k]
 clean(root);return ET.tostring(root,encoding='utf-8')

def svg_image(source,max_edge=1600):
 import pymupdf
 raw=safe_svg(Path(source).read_bytes())
 with pymupdf.open(stream=raw,filetype='svg')as doc:
  p=doc[0];scale=min(max_edge/max(p.rect.width,p.rect.height),math.sqrt(MAX_PIXELS/(p.rect.width*p.rect.height)));pix=p.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False);return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)

def budget_cache(keep):
 # Evict only PNG files explicitly created in this task-owned cache.
 records=CACHE/'owned.json';owned=json.loads(records.read_text())if records.exists()else[];owned=[n for n in owned if(CACHE/n).is_file()]
 if keep.name not in owned:owned.append(keep.name)
 total=sum((CACHE/n).stat().st_size for n in owned)
 for name in list(owned):
  if total<=MAX_CACHE_BYTES and len(owned)<=512:break
  if name==keep.name:continue
  p=CACHE/name;total-=p.stat().st_size;p.unlink();owned.remove(name)
  metadata=p.with_suffix('.json')
  if metadata.exists():metadata.unlink()
 write_json(records,owned)

def placeholder(message):
 im=Image.new('RGB',(1000,600),'#edf2f5');d=ImageDraw.Draw(im);d.text((35,220),message,fill='#29434f');return im

def preview(source,page=1,edge=1400):
 source=Path(source);key=hashlib.sha256(json.dumps([sha(source)if source.is_file()else str(source),page,edge,'source-preview-v1']).encode()).hexdigest();dest=CACHE/(key+'.png')
 with LOCK:
  if dest.exists():
   with Image.open(dest)as im:size=im.size
   return dest,{'page':page,'width':size[0],'height':size[1]}
  if not source.is_file():im=placeholder('Source asset unavailable. Recorded answer is retained.')
  elif source.suffix.lower()=='.pdf':
   import pymupdf
   with pymupdf.open(source)as doc:
    p=doc[page-1];scale=edge/max(p.rect.width,p.rect.height);pix=p.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
  elif source.suffix.lower()=='.svg':im=svg_image(source,edge)
  elif source.suffix.lower()=='.ifc':im=placeholder('IFC model context is loading; recorded GUID/property evidence remains available.')
  else:im=ImageOps.exif_transpose(Image.open(source)).convert('RGB');im.thumbnail((edge,edge))
  im.save(dest);budget_cache(dest);return dest,{'page':page,'width':im.width,'height':im.height}

def page_info(source):
 source=Path(source)
 if not source.exists():return[{'page':1,'width':1000,'height':600,'scale':1,'coordinate_system':'Missing source placeholder, no spatial correspondence'}]
 if source.suffix.lower()=='.pdf':
  import pymupdf
  with pymupdf.open(source)as d:return[{'page':i+1,'width':round(p.rect.width*1400/max(p.rect.width,p.rect.height)),'height':round(p.rect.height*1400/max(p.rect.width,p.rect.height)),'scale':1400/max(p.rect.width,p.rect.height),'rotation':p.rotation,'coordinate_system':'displayed PDF preview pixels; source evidence unrotated points'}for i,p in enumerate(d)]
 if source.suffix.lower()=='.ifc':return[{'page':1,'width':1000,'height':600,'scale':1,'coordinate_system':'IFC model context, no image localization'}]
 if source.suffix.lower()=='.svg':
  import pymupdf
  raw=safe_svg(source.read_bytes());r=ET.fromstring(raw);vb=[float(v)for v in r.get('viewBox','').replace(',',' ').split()]
  with pymupdf.open(stream=raw,filetype='svg')as d:
   p=d[0];scale=1400/max(p.rect.width,p.rect.height)
   return[{'page':1,'width':round(p.rect.width*scale),'height':round(p.rect.height*scale),'scale':scale,'svg_viewBox':vb if len(vb)==4 else[0,0,p.rect.width,p.rect.height],'svg_css_size':[p.rect.width,p.rect.height],'coordinate_system':'Sanitized SVG viewBox mapped to raster preview; external resources disabled'}]
 else:
  im=ImageOps.exif_transpose(Image.open(source));w,h=im.size
 scale=min(1,1400/max(w,h));return[{'page':1,'width':round(w*scale),'height':round(h*scale),'scale':scale,'coordinate_system':'source image pixels scaled to lightweight preview'}]

def boxes_for(pred,pages,source):
 boxes=[];suffix=Path(source).suffix.lower()
 if suffix=='.ifc'or not Path(source).is_file():return boxes
 doc=None
 if suffix=='.pdf':
  import pymupdf
  doc=pymupdf.open(source)
 try:
  for e in pred.get('evidence',[]):
   if not isinstance(e.get('bbox'),list)or len(e['bbox'])!=4:continue
   pn=e.get('page',1)
   if type(pn)!=int or not 1<=pn<=len(pages):continue
   b=e['bbox'];p=pages[pn-1];scale=p.get('scale',1)
   if doc:
    import pymupdf
    b=list(pymupdf.Rect(b)*doc[pn-1].rotation_matrix*pymupdf.Matrix(scale,scale))
   elif suffix=='.svg':
    vb=p['svg_viewBox'];cw,ch=p['svg_css_size'];b=[(b[0]-vb[0])*cw/vb[2]*scale,(b[1]-vb[1])*ch/vb[3]*scale,(b[2]-vb[0])*cw/vb[2]*scale,(b[3]-vb[1])*ch/vb[3]*scale]
   else:b=[v*scale for v in b]
   if not all(isinstance(v,(int,float))and math.isfinite(v)for v in b):continue
   b=[max(0,min(p['width'],b[0])),max(0,min(p['height'],b[1])),max(0,min(p['width'],b[2])),max(0,min(p['height'],b[3]))]
   if b[0]<b[2]and b[1]<b[3]:boxes.append({'xyxy':b,'page':pn,'included':True,'evidence_id':e.get('id'),'class_name':e.get('class',e.get('kind','evidence')),'detector_score':e.get('score')})
 finally:
  if doc:doc.close()
 return boxes

def crop(source,page,bbox,preview_page,dpi=288):
 """bbox is current displayed-preview pixels; supports saved/unsaved human edits."""
 source=Path(source)
 if not source.is_file():raise ValueError('Source asset unavailable; recorded answer is unchanged')
 if len(bbox)!=4 or not all(math.isfinite(v)for v in bbox):raise ValueError('Invalid source region')
 x1,y1,x2,y2=bbox;w,h=preview_page['width'],preview_page['height']
 if not 0<=x1<x2<=w+1 or not 0<=y1<y2<=h+1:raise ValueError('Region outside page preview')
 scale=preview_page.get('scale',1);source_bbox=[v/scale for v in bbox];identity={'source_sha256':sha(source),'page':page,'display_bbox':source_bbox,'dpi':dpi,'pixel_budget':MAX_PIXELS,'version':'original-crop-v1'};key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();dest=CACHE/(key+'.png');meta=CACHE/(key+'.json')
 with LOCK:
  if dest.exists()and meta.exists():return dest,json.loads(meta.read_text())
  if source.suffix.lower()in ['.pdf','.svg']:
   import pymupdf
   document=pymupdf.open(stream=safe_svg(source.read_bytes()),filetype='svg')if source.suffix.lower()=='.svg'else pymupdf.open(source)
   with document as d:
    p=d[page-1];b=pymupdf.Rect(source_bbox);pad=max(10,min(35,max(b.width,b.height)*.15));clip=(b+(-pad,-pad,pad,pad))&p.rect;ratio=min(dpi/72,2048/max(clip.width,clip.height),math.sqrt(MAX_PIXELS/(clip.width*clip.height)));pix=p.get_pixmap(matrix=pymupdf.Matrix(ratio,ratio),clip=clip,alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);offset=[b.x0-clip.x0,b.y0-clip.y0,b.x1-clip.x0,b.y1-clip.y0];highlight=[v*ratio for v in offset];info=dict(identity,effective_dpi=ratio*72,unrotated_evidence_bbox=list(b*p.derotation_matrix),display_clip=list(clip),source_rotation=p.rotation,original_crop_render=True)
  else:
   im=svg_image(source,2048)if source.suffix.lower()=='.svg'else ImageOps.exif_transpose(Image.open(source)).convert('RGB');b=source_bbox;pad=max(18,min(120,max(b[2]-b[0],b[3]-b[1])*.25));clip=[max(0,math.floor(b[0]-pad)),max(0,math.floor(b[1]-pad)),min(im.width,math.ceil(b[2]+pad)),min(im.height,math.ceil(b[3]+pad))];im=im.crop(clip);ratio=min(1,2048/max(im.size),math.sqrt(MAX_PIXELS/(im.width*im.height)));highlight=[(b[0]-clip[0])*ratio,(b[1]-clip[1])*ratio,(b[2]-clip[0])*ratio,(b[3]-clip[1])*ratio]
   if ratio<1:im=im.resize((round(im.width*ratio),round(im.height*ratio)))
   info=dict(identity,effective_dpi=None,source_clip=clip,original_crop_render=True,upscaled=False)
  draw=ImageDraw.Draw(im);draw.rectangle(highlight,outline='#ff00c8',width=3);im.save(dest);info.update(width=im.width,height=im.height,cache_key=key);write_json(meta,info);budget_cache(dest);return dest,info
