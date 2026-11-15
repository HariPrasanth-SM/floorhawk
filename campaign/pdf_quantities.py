"""Recover missing areas from intrinsic closed native rectangles/quads + printed scale.
Printed values stay primary. No inferred raster scale, room database or IFC lookup.
"""
import math,re,copy
from pathlib import Path
from qa.common import sha
VERSION='native-prefixed-rooms-closed-areas-v3'
def recover(file,facts=None):
 import pymupdf
 from shapely.geometry import Polygon,Point
 from qa.pdf import parse_pdf
 result=copy.deepcopy(facts if facts is not None else parse_pdf(file,room_id_pattern=re.compile(r'^[A-Z]?\d{1,2}\.\d{2}$')));recovered=[]
 with pymupdf.open(file)as doc:
  for pn,page in enumerate(doc):
   ratios={int(v)for v in re.findall(r'1\s*:\s*(\d+)',page.get_text())}
   if len(ratios)!=1:continue
   ratio=next(iter(ratios));rooms=[e for e in result['entities']if e.get('kind')=='room'and e.get('page',1)==pn+1];boundaries=[]
   for i,path in enumerate(page.get_drawings()):
    fill=path.get('fill');items=path['items']
    if not fill or min(fill)<.85 or not items:continue
    item=items[0]
    if item[0]=='re':
     b=item[1];points=[(b.x0,b.y0),(b.x1,b.y0),(b.x1,b.y1),(b.x0,b.y1)]
    elif item[0]=='qu':points=[tuple(q)for q in[item[1].ul,item[1].ur,item[1].lr,item[1].ll]]
    elif all(x[0]=='l'for x in items):
     if any(math.dist(tuple(a[2]),tuple(b[1]))>.1 for a,b in zip(items,items[1:])):continue
     points=[tuple(items[0][1])]+[tuple(x[2])for x in items]
    else:continue
    poly=Polygon(points)
    if not poly.is_valid or not 10<poly.area<page.rect.width*page.rect.height*.8:continue
    boundaries.append((poly,i,item[0]))
   for e in rooms:
    if e.get('area_m2')is not None:continue
    b=e['bbox'];anchor=Point((b[0]+b[2])/2,(b[1]+b[3])/2);candidates=[]
    for poly,i,kind in boundaries:
     if not poly.covers(anchor):continue
     other=[o for o in rooms if o['id']!=e['id']and poly.covers(Point((o['bbox'][0]+o['bbox'][2])/2,(o['bbox'][1]+o['bbox'][3])/2))]
     if other:continue
     candidates.append((poly,i,kind))
    if not candidates:continue
    candidates.sort(key=lambda x:x[0].area);poly,i,kind=candidates[0]
    if len(candidates)>1 and candidates[1][0].symmetric_difference(poly).area/poly.area>.001:continue
    area=poly.area*(ratio*.0254/72)**2;e.update(area_m2=area,area_method='closed native filled '+kind+' room polygon at explicit printed1:'+str(ratio)+' scale; assumes original physical PDF size',room_polygon_points=[list(p)for p in poly.exterior.coords],area_geometry_path_index=i,area_geometry_version=VERSION);recovered.append({'entity_id':e['id'],'native_path_index':i,'shape':kind,'value_m2':area,'polygon':[list(p)for p in poly.exterior.coords]})
 result['closed_room_geometry_recovery']={'version':VERSION,'recovered':recovered,'source_sha256':sha(file),'warnings':['Derived area assumes original PDF physical dimensions and explicit printed scale; no raster pixel calibration or hidden-room inference.']};return result

def answer(file,task,question=""):
 if task.get('operation')!='area'or task.get('target')not in['room','apartment']or task.get('scope')=='model':return None
 from qa.tools import pdf_answer
 facts=recover(file);r=pdf_answer(facts,task,question)
 if r['status']!='success':return None
 r.update(route='pdf.closed-rectangle-room-areas.campaign-v1',closed_room_geometry_recovery=facts['closed_room_geometry_recovery']);return r
