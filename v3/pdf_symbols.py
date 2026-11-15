from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Native PDF fixture matching against the drawing's own labelled legend.
Matches compound vector geometry, not room labels or expected counts. Affine
normalization handles rotation/scale. Similarity is not calibrated probability.
"""
import hashlib,json,time,math
import numpy as np
from qa.common import ROOT,sha,write_json,norm
VERSION='native-legend-compound-v2'
LABELS={'wc':'toilet_fixture','lavabo':'sink','badewanne':'bathtub','dusche':'shower','fenster':'window','ture':'door'}
def points(d):
 out=[]
 for item in d['items']:
  if item[0] in ('l','c'):out.extend([list(p) for p in item[1:]])
  elif item[0]=='qu':out.extend([list(p) for p in (item[1].ul,item[1].ur,item[1].lr,item[1].ll)])
  elif item[0]=='re':r=item[1];out.extend([[r.x0,r.y0],[r.x1,r.y0],[r.x1,r.y1],[r.x0,r.y1]])
 return np.array(out,dtype=float).reshape(-1,2)
def signature(d):return (len(d['items']),tuple(sorted(set(i[0] for i in d['items']))))
def quad(d):
 if len(d['items'])==1 and d['items'][0][0]=='re':
  r=d['items'][0][1];a=np.array([[r.x0,r.y0],[r.x1,r.y0],[r.x1,r.y1],[r.x0,r.y1]])
 elif len(d['items'])==1 and d['items'][0][0]=='qu':
  q=d['items'][0][1];a=np.array([list(q.ul),list(q.ur),list(q.lr),list(q.ll)])
 elif len(d['items'])==4 and all(i[0]=='l' for i in d['items']):a=np.array([list(i[1]) for i in d['items']],dtype=float)
 else:return None
 B=np.stack([a[1]-a[0],a[3]-a[0]],axis=1)
 if abs(np.linalg.det(B))<.01 or np.linalg.norm(a[0]+a[2]-a[1]-a[3])>.01:return None
 return a[0],np.linalg.inv(B)
def descriptor(d,basis):
 z=(points(d)-basis[0])@basis[1].T
 if not len(z) or z.min()<-.02 or z.max()>1.02:return None
 span=z.max(0)-z.min(0);off=np.abs((z.max(0)+z.min(0))/2-.5);return np.r_[np.sort(span),np.sort(off)]

def parse(file):
 import pymupdf
 source=sha(file);cache=CACHE_ROOT/'v3-pdf-symbols'/(source+'-'+VERSION+'-'+sha(ROOT/'v3/pdf_symbols.py')[:16]+'.json');started=time.perf_counter()
 if cache.exists():r=json.loads(cache.read_text());r['cache_hit']=True;r['retrieval_seconds']=time.perf_counter()-started;return r
 with pymupdf.open(file) as doc:
  if len(doc)!=1:raise ValueError('Native fixture matcher supports one page')
  page=doc[0];words=page.get_text('words');heads=[w for w in words if norm(w[4]) in ('legende','legend')]
  if len(heads)!=1:raise ValueError('One explicit native symbol legend is required')
  heading=heads[0];legend_y=heading[1];draw=page.get_drawings()
  if len(draw)>20000:raise ValueError('PDF too complex for bounded native symbol matching')
  boxes=np.array([list(d['rect']) for d in draw],dtype=float);sigs=[signature(d) for d in draw];quads={i:quad(d) for i,d in enumerate(draw)};quads={i:b for i,b in quads.items() if b is not None};templates={}
  def inside(i):
   b=boxes[i];return np.flatnonzero((boxes[:,0]>=b[0]-.05)&(boxes[:,1]>=b[1]-.05)&(boxes[:,2]<=b[2]+.05)&(boxes[:,3]<=b[3]+.05))
  for label,cls in LABELS.items():
   if cls in ('window','door'):continue
   labels=[w for w in words if norm(w[4])==label and legend_y<w[1]<legend_y+page.mediabox.height*.2]
   if len(labels)!=1:continue
   word=labels[0];cy=(word[1]+word[3])/2;candidates=[i for i in quads if boxes[i,2]<word[0] and word[0]-boxes[i,2]<35 and abs((boxes[i,1]+boxes[i,3])/2-cy)<8 and boxes[i,2]-boxes[i,0]<35 and boxes[i,3]-boxes[i,1]<20]
   if not candidates:continue
   outer=max(candidates,key=lambda i:(boxes[i,2]-boxes[i,0])*(boxes[i,3]-boxes[i,1]));children=[i for i in inside(outer) if i!=outer];primary_sig=(47,('l',)) if cls in ('sink','toilet_fixture') else (68,('l',)) if cls=='bathtub' else (8,('c',));primaries=[i for i in children if sigs[i]==primary_sig]
   if len(primaries)!=1:continue
   desc=descriptor(draw[primaries[0]],quads[outer])
   if desc is None:continue
   secondary=(8,('c',)) if cls=='bathtub' else (1,('qu',)) if cls=='shower' else None
   if secondary and not any(sigs[i]==secondary for i in children):continue
   templates[cls]={'primary_signature':[primary_sig[0],list(primary_sig[1])],'descriptor':desc.tolist(),'secondary_signature':[secondary[0],list(secondary[1])] if secondary else None,'legend_bbox':boxes[outer].tolist(),'legend_label':word[4]}
  for label,cls in [('fenster','window'),('ture','door')]:
   hits=[w for w in words if norm(w[4])==label and legend_y<w[1]<legend_y+page.mediabox.height*.2]
   if len(hits)!=1:continue
   word=hits[0];cy=(word[1]+word[3])/2;near=[i for i,d in enumerate(draw) if boxes[i,2]<word[0] and word[0]-boxes[i,2]<40 and abs((boxes[i,1]+boxes[i,3])/2-cy)<8 and boxes[i,2]-boxes[i,0]<40 and boxes[i,3]-boxes[i,1]<25]
   if cls=='door':
    if not any(sigs[i]==(2,('c',)) for i in near) or not any(sigs[i]==(1,('l',)) for i in near):continue
    templates[cls]={'legend_label':word[4],'method':'quarter-circle arc with connected leaf','legend_path_indices':near}
   else:
    accepted=None
    for outer in [i for i in near if i in quads]:
     offsets=[]
     for child in inside(outer):
      if sigs[child]!=(1,('l',)):continue
      z=(points(draw[child])-quads[outer][0])@quads[outer][1].T;span=np.abs(z[1]-z[0])
      if span[0]>.97 and span[1]<.02 and .05<z[:,1].mean()<.95:offsets.append(float(z[:,1].mean()))
      elif span[1]>.97 and span[0]<.02 and .05<z[:,0].mean()<.95:offsets.append(float(z[:,0].mean()))
     if len(offsets)==2 and max(abs(a-b) for a,b in zip(sorted(offsets),[.335,.665]))<.025:accepted=(outer,sorted(offsets))
    if accepted:templates[cls]={'legend_label':word[4],'method':'parallel-third-lines in closed frame','legend_bbox':boxes[accepted[0]].tolist(),'normalized_offsets':accepted[1]}

  if not templates:raise ValueError('Legend geometry is not a supported compound-symbol style')
  entities=[];rejected=[]
  for outer,basis in quads.items():
   b=boxes[outer]
   if b[3]>=legend_y-2 or b[2]-b[0]>.15*page.mediabox.width or b[3]-b[1]>.15*page.mediabox.height:continue
   children=[i for i in inside(outer) if i!=outer];matches=[]
   for cls,t in templates.items():
    if 'primary_signature' not in t:continue
    sig=(t['primary_signature'][0],tuple(t['primary_signature'][1]));secondary=(t['secondary_signature'][0],tuple(t['secondary_signature'][1])) if t['secondary_signature'] else None
    if secondary and not any(sigs[i]==secondary for i in children):continue
    for child in children:
     if sigs[child]!=sig:continue
     value=descriptor(draw[child],basis)
     if value is None:continue
     expected=np.array(t['descriptor']);error=float(np.max(np.abs(value-expected)))
     if cls=='shower':error=max(abs(float(max(value[:2]))-max(expected[:2])),float(max(value[2:])))
     tolerance=.035 if cls in ('bathtub','shower') else .02
     if error<tolerance:matches.append((error,cls,child,tolerance))
   if not matches:continue
   matches.sort()
   if len({m[1] for m in matches})!=1:rejected.append({'outer_path_index':outer,'reason':'ambiguous legend classes'});continue
   error,cls,child,tol=matches[0];entities.append({'id':f'native-symbol-{outer}','kind':'native_fixture_symbol','class':cls,'bbox':b.tolist(),'page':1,'included':True,'score':max(0.,1-error/tol),'template_similarity_error':error,'native_path_indices':[int(outer),int(child)],'coordinate_system':'PDF unrotated points','source_sha256':source,'provenance':'Compound native vector geometry matches this document’s labelled '+templates[cls]['legend_label']+' legend symbol; similarity score is not calibrated probability'})
  if 'window' in templates:
   for outer,basis in quads.items():
    b=boxes[outer];bw,bh=b[2]-b[0],b[3]-b[1]
    if b[3]>=legend_y-2 or min(bw,bh)<.2 or max(bw,bh)/min(bw,bh)<1.3:continue
    offsets=[];used=[]
    for child in inside(outer):
     if sigs[child]!=(1,('l',)):continue
     z=(points(draw[child])-basis[0])@basis[1].T
     if len(z)!=2:continue
     span=np.abs(z[1]-z[0])
     if span[0]>.97 and span[1]<.02 and .05<z[:,1].mean()<.95:offsets.append(float(z[:,1].mean()));used.append(int(child))
     elif span[1]>.97 and span[0]<.02 and .05<z[:,0].mean()<.95:offsets.append(float(z[:,0].mean()));used.append(int(child))
    if len(offsets)!=2:continue
    error=float(np.max(np.abs(np.sort(offsets)-np.array(templates['window']['normalized_offsets']))))
    if error>.025:continue
    entities.append({'id':f'native-window-{outer}','kind':'native_opening_symbol','class':'window','bbox':b.tolist(),'page':1,'included':True,'score':max(0.,1-error/.025),'template_similarity_error':error,'native_path_indices':[int(outer)]+used,'coordinate_system':'PDF unrotated points','source_sha256':source,'provenance':'Closed frame with two full-span parallel third-lines matches the supplied Fenster legend; not pane counting or calibrated probability'})
  if 'door' in templates:
   lines=[i for i in range(len(draw)) if sigs[i]==(1,('l',)) and boxes[i,3]<legend_y-2]
   for i,d in enumerate(draw):
    if sigs[i]!=(2,('c',)) or boxes[i,3]>=legend_y-2:continue
    a=np.array(d['items'][0][1]);b=np.array(d['items'][-1][-1]);chord=np.linalg.norm(a-b)
    if chord<.5:continue
    radius=chord/math.sqrt(2);matches=[]
    for leaf in lines:
     ends=points(draw[leaf]);dist_a=np.linalg.norm(ends-a,axis=1);dist_b=np.linalg.norm(ends-b,axis=1)
     if min(dist_a.min(),dist_b.min())>.02*radius:continue
     near=int(np.argmin(np.minimum(dist_a,dist_b)));hinge=ends[1-near];u=a-hinge;v=b-hinge;error=max(abs(np.linalg.norm(u)-radius)/radius,abs(np.linalg.norm(v)-radius)/radius,abs(float(u@v))/(radius*radius))
     if error<.03:matches.append((error,leaf))
    if not matches:continue
    error,leaf=min(matches);bb=[min(boxes[i,0],boxes[leaf,0]),min(boxes[i,1],boxes[leaf,1]),max(boxes[i,2],boxes[leaf,2]),max(boxes[i,3],boxes[leaf,3])];entities.append({'id':f'native-door-{i}','kind':'native_opening_symbol','class':'door','bbox':list(map(float,bb)),'page':1,'included':True,'score':max(0.,1-error/.03),'template_similarity_error':float(error),'native_path_indices':[i,int(leaf)],'coordinate_system':'PDF unrotated points','source_sha256':source,'provenance':'Quarter-circle swing arc plus connected straight leaf matches the supplied Türe legend; one drawn swing symbol per proposal, not calibrated probability'})
  # Nested duplicate parent paths must not make a second fixture.
  from .dedup import suppress
  entities,duplicates=suppress(entities,'fragments85')
  r={'source_sha256':source,'entities':entities,'templates':templates,'ambiguous':rejected,'duplicates':duplicates,'version':VERSION,'legend_y':legend_y,'timing_seconds':time.perf_counter()-started,'cache_hit':False};write_json(cache,r);return r

def answer(file,task):
 wanted=['shower','bathtub'] if task.get('target')=='shower_bath' else [task.get('target')]
 if task.get('operation')!='count' or task.get('scope')!='drawing' or task.get('filters') or any(t not in LABELS.values() for t in wanted):return None
 r=parse(file)
 if any(t not in r['templates'] for t in wanted):return None
 entities=[e for e in r['entities'] if e['class'] in wanted]
 return {'status':'success','answer':len(entities),'unit':'count','evidence':entities,'route':'pdf.native-legend-symbols.v3','device':'cpu','model':{'name':'Native PDF labelled-legend compound-vector matcher','source_revision':sha(ROOT/'v3/pdf_symbols.py'),'template_sha256':hashlib.sha256(json.dumps(r['templates'],sort_keys=True).encode()).hexdigest(),'class_map':LABELS,'weights':'No pretrained neural weights for this route; templates come from the supplied drawing'},'native_symbol_timing':{'extraction_seconds_original':r['timing_seconds'],'cache_hit':r['cache_hit']},'native_symbol_settings':{'version':VERSION,'templates':r['templates'],'legend_excluded':True},'warnings':['Supported compound native-vector legend styles only; raster/scanned symbols and different glyph constructions may be missed.','Template similarity is not calibrated probability. Zero does not verify absence. Count agreement is not localization precision/recall.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in entities],'value':len(entities)}]}
