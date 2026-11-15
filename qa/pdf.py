"""Native PDF evidence with room/area associations; no annotation sidecars."""
import math,re
from .common import bbox_union,norm
AREA=re.compile(r'^(\d+(?:[.,]\d+)?)\s*m[²2]$')
ROOM_ID=re.compile(r'^\d{1,2}\.\d{2}$')
APARTMENT=re.compile(r'^(?:Whg\.?\s*|Wohnung\s+|App\.?\s+|Appartement\s+|Logement\s+|Appartamento\s+|Apartment\s+|Apt\.?\s+)([A-Z]|\d{1,3})$',re.I)

def lines_from_page(page):
 lines=[]
 for block in page.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   spans=line['spans'];text=''.join(s['text'] for s in spans).strip()
   if text:lines.append({'text':text,'bbox':list(line['bbox']),'method':'native PDF text'})
 return lines

def parse_pdf(path,room_id_pattern=None):
 room_id=room_id_pattern or ROOM_ID
 import pymupdf
 from shapely.geometry import Point,Polygon
 doc=pymupdf.open(path);pages=[];entities=[];warnings=[]
 for pn,page in enumerate(doc):
  lines=lines_from_page(page);words=[{'text':w[4],'bbox':list(w[:4]),'page':pn+1} for w in page.get_text('words')]
  if not words:
   from .raster import ocr_image
   from .common import CACHE
   image=CACHE/(str(pn)+'-ocr-'+path.stem+'.png');scale=min(2,1800/max(page.rect.width,page.rect.height));page.get_pixmap(matrix=pymupdf.Matrix(scale,scale)).save(image)
   for w in ocr_image(image):
    rect=pymupdf.Rect(w['bbox'])/pymupdf.Matrix(scale,scale);rect=rect*page.derotation_matrix
    lines.append({'text':w['text'],'bbox':list(rect),'method':'OCR inferred line association'});words.append({'text':w['text'],'bbox':list(rect),'page':pn+1})
   warnings.append(f'Page {pn+1} used English OCR; text/area associations may be incomplete.')
  pages.append({'page':pn+1,'width_points':page.rect.width,'height_points':page.rect.height,'unrotated_size':list(page.mediabox),'rotation':page.rotation,'lines':lines,'words':words,'text':page.get_text(),'vector_paths':len(page.get_drawings())})
  ids=[l for l in lines if room_id.fullmatch(l['text'])];areas=[l for l in lines if AREA.fullmatch(l['text'])]
  label_candidates=[l for l in lines if not AREA.fullmatch(l['text']) and not room_id.fullmatch(l['text']) and not APARTMENT.fullmatch(l['text']) and any(c.isalpha() for c in l['text'])]
  apartments=[]
  for l in lines:
   match=APARTMENT.fullmatch(l['text'])
   if match:apartments.append({'id':f'pdf-{pn+1}-apt-{match[1]}','kind':'apartment','class':'apartment','label':match[1],'page':pn+1,'bbox':l['bbox'],'text':l['text'],'coordinate_system':'PDF unrotated points','method':'explicit apartment label'})
  boundaries=[]
  room_shapes=[]
  scale_values={int(v) for v in re.findall(r'1\s*:\s*(\d+)',page.get_text())}
  scale_ratio=next(iter(scale_values)) if len(scale_values)==1 else None
  for drawing in page.get_drawings():
   if drawing.get('fill') is None or len(drawing['items'])<3:continue
   items=drawing['items']
   if not all(item[0]=='l' for item in items):continue
   points=[tuple(items[0][1])]+[tuple(item[2]) for item in items]
   if not drawing.get('closePath') and math.dist(points[0],points[-1])>2:continue
   poly=Polygon(points)
   if poly.is_valid and poly.area>10 and poly.area<page.rect.width*page.rect.height*.8:room_shapes.append(poly)
  # A non-gray polygon enclosing exactly one explicit apartment anchor supplies geometric membership.
  for drawing in page.get_drawings():
   color=drawing.get('color');items=drawing['items']
   if not color or max(color)-min(color)<.1 or len(items)<4 or not all(i[0]=='l' for i in items):continue
   points=[tuple(items[0][1])]+[tuple(i[2]) for i in items]
   if math.dist(points[0],points[-1])>3:continue
   poly=Polygon(points)
   if not poly.is_valid:continue
   inside=[a for a in apartments if poly.buffer(2).contains(Point((a['bbox'][0]+a['bbox'][2])/2,(a['bbox'][1]+a['bbox'][3])/2))]
   if len(inside)==1:boundaries.append((poly,inside[0]['label']))
  for ident in ids:
   b=ident['bbox'];cx=(b[0]+b[2])/2
   below=[l for l in areas if -1<=l['bbox'][1]-b[3]<=25 and abs((l['bbox'][0]+l['bbox'][2])/2-cx)<30]
   above=[l for l in label_candidates if -1<=b[1]-l['bbox'][3]<=25 and abs((l['bbox'][0]+l['bbox'][2])/2-cx)<35]
   if not above:continue
   area=min(below,key=lambda l:abs(l['bbox'][1]-b[3])+abs((l['bbox'][0]+l['bbox'][2])/2-cx)) if below else None;label=min(above,key=lambda l:abs(b[1]-l['bbox'][3])+abs((l['bbox'][0]+l['bbox'][2])/2-cx))
   value=float(AREA.fullmatch(area['text'])[1].replace(',','.')) if area else None
   area_method='printed numeric area' if area else 'unavailable'
   containing=[p for p in room_shapes if p.covers(Point(cx,(b[1]+b[3])/2))]
   room_poly=min(containing,key=lambda p:p.area) if containing else None
   if value is None and room_poly is not None and scale_ratio is not None:
    value=room_poly.area*(scale_ratio*.0254/72)**2
    area_method='vector polygon at explicit printed 1:'+str(scale_ratio)+' scale; assumes original physical PDF page size'
   box=bbox_union([b,label['bbox']]+([area['bbox']] if area else []));groups=[a for poly,a in boundaries if poly.buffer(.5).contains(Point(cx,(b[1]+b[3])/2))]
   entities.append({'id':f'pdf-{pn+1}-room-{ident["text"]}','kind':'room','class':'labelled_room','room_number':ident['text'],'label':label['text'],'area_m2':value,'area_method':area_method,'room_polygon_points':list(room_poly.exterior.coords) if room_poly is not None else None,'apartment':groups[0] if len(groups)==1 else None,'apartment_association':'explicit label enclosed by colored vector boundary' if len(groups)==1 else 'unresolved','page':pn+1,'bbox':box,'text':' | '.join([label['text'],ident['text']]+([area['text']] if area else [])),'coordinate_system':'PDF unrotated points','method':'native text; nearest aligned label/ID/printed area association'})
  entities.extend(apartments)
 # Identical IDs on the same page indicate ambiguity, not extra rooms.
 seen={};dedup=[]
 for e in entities:
  if e['id'] in seen:warnings.append('Duplicate room ID on one page; room count is ambiguous: '+e['id']);continue
  seen[e['id']]=e;dedup.append(e)
 return {'kind':'pdf','entities':dedup,'pages':pages,'warnings':warnings+['Only numbered labelled rooms are counted; areas require printed values or a closed vector room polygon and explicit scale. Legends and schedule rows are not room instances.','Apartment membership requires an enclosing explicit vector boundary; otherwise apartment sums abstain.','PDF view does not imply access to the full associated IFC model.'],'tool':'PyMuPDF','coordinate_system':'PDF unrotated points; use page.rotation_matrix for displayed pixel evidence'}
