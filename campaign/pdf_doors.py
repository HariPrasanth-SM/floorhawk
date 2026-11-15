"""Native PDF door swing/leaf geometry across separate and compound paths.
Templates and geometry from the supplied PDF only; no associated IFC or answers.
"""
import math,json,time,hashlib
from pathlib import Path
import numpy as np
from qa.common import sha
from .clock import atomic
VERSION='native-swing-compound-paths-v2'
def parse(file):
 import pymupdf
 from v3.pdf_symbols import parse as legend_parse
 source=sha(file);facts=legend_parse(file)
 if 'door'not in facts.get('templates',{}):raise ValueError('No explicit supported door legend')
 with pymupdf.open(file)as doc:
  if len(doc)!=1:raise ValueError('Single-page native geometry only')
  page=doc[0];draw=page.get_drawings();legend_y=facts['legend_y'];lines=[];curves=[];signatures={}
  for pi,path in enumerate(draw):
   if path['rect'].y1>=legend_y-2:continue
   run=[]
   def finish():
    if run:curves.append((pi,list(run)))
   for item in path['items']:
    if item[0]=='l':
     finish();run=[];a=np.asarray(item[1],dtype=float);b=np.asarray(item[2],dtype=float)
     if np.linalg.norm(a-b)>.3:lines.append((pi,a,b))
    elif item[0]=='c':
     points=np.asarray([list(x)for x in item[1:]],dtype=float)
     if run and np.linalg.norm(run[-1][-1]-points[0])>.02:finish();run=[]
     run.append(points)
    else:finish();run=[]
   finish()
  if not lines:return {'source_sha256':source,'entities':[],'status':'success','version':VERSION}
  ends=np.asarray([[a,b]for _,a,b in lines]);entities=[];rejected=0
  for pi,segments in curves:
   a,b=segments[0][0],segments[-1][-1];chord=np.linalg.norm(a-b)
   if chord<.5:continue
   radius=chord;distance=np.minimum(np.linalg.norm(ends-a,axis=2),np.linalg.norm(ends-b,axis=2));near_lines=np.flatnonzero(distance.min(1)<.03*radius);best=None
   for li in near_lines:
    near=int(np.argmin(distance[li]));hinge=ends[li,1-near];u=a-hinge;v=b-hinge;radius=float(np.linalg.norm(ends[li,near]-hinge));angle=math.degrees(math.acos(float(np.clip((u@v)/max(np.linalg.norm(u)*np.linalg.norm(v),1e-9),-1,1))))
    if radius<.5 or not 20<=angle<=175:continue
    error=max(abs(np.linalg.norm(u)-radius)/radius,abs(np.linalg.norm(v)-radius)/radius)
    if error>.04:continue
    radial=0
    for segment in segments:
     for t in [.2,.4,.6,.8]:
      point=(1-t)**3*segment[0]+3*(1-t)**2*t*segment[1]+3*(1-t)*t*t*segment[2]+t**3*segment[3];radial=max(radial,abs(np.linalg.norm(point-hinge)-radius)/radius)
    if radial>.04:continue
    if best is None or error+radial<best[0]:best=(error+radial,int(li),hinge)
   if best is None:rejected+=1;continue
   error,li,hinge=best;points=np.concatenate(segments+[ends[li]],axis=0);bb=[float(points[:,0].min()),float(points[:,1].min()),float(points[:,0].max()),float(points[:,1].max())]
   if any(np.linalg.norm(np.asarray(e['hinge'])-hinge)<.05*radius and max(abs(x-y)for x,y in zip(e['bbox'],bb))<.1*radius for e in entities):continue
   entities.append({'id':f'compound-door-{pi}-{len(entities)+1}','class':'door','kind':'native_opening_symbol','bbox':bb,'page':1,'source_sha256':source,'coordinate_system':'PDF unrotated points','native_path_indices':[pi,lines[li][0]],'curve_segments':len(segments),'hinge':hinge.tolist(),'arc_endpoints':[a.tolist(),b.tolist()],'radius':float(radius),'geometry_error':float(error),'provenance':'Circular quarter-swing and connected leaf verified across native compound paths, using explicit Türe legend; not a probability'})
  # Two opposing leaves with a shared closed endpoint describe one physical opening.
  grouped=[];used=set()
  for i,e in enumerate(entities):
   if i in used:continue
   pair=None
   for j,k in enumerate(entities):
    if j<=i or j in used:continue
    r=e['radius']+k['radius'];hinge_distance=np.linalg.norm(np.asarray(e['hinge'])-np.asarray(k['hinge']));endpoint_distance=min(np.linalg.norm(np.asarray(a)-np.asarray(b))for a in e['arc_endpoints']for b in k['arc_endpoints'])
    if abs(hinge_distance-r)<.06*r and endpoint_distance<.03*min(e['radius'],k['radius']):pair=j;break
   if pair is not None:
    k=entities[pair];used.add(pair);e=dict(e,id=e['id']+'-double',bbox=[min(e['bbox'][0],k['bbox'][0]),min(e['bbox'][1],k['bbox'][1]),max(e['bbox'][2],k['bbox'][2]),max(e['bbox'][3],k['bbox'][3])],leaf_ids=[e['id'],k['id']],provenance='Two opposing native leaf/swing instances share one closing point: one double-leaf opening')
   grouped.append(e)
 return {'status':'success','source_sha256':source,'entities':grouped,'ungrouped_entities':entities,'curved_path_runs':len(curves),'rejected_nonquarter_geometry':rejected,'legend_support':facts['templates']['door'],'version':VERSION}
