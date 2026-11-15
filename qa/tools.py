"""Registered evidence queries and deterministic arithmetic. No model-generated code."""
import re
from .common import norm
IFC_CLASSES={'window':'IfcWindow','door':'IfcDoor','room':'IfcSpace','wall':'IfcWall','stair':'IfcStair','storey':'IfcBuildingStorey','building':'IfcBuilding','column':'IfcColumn','beam':'IfcBeam','slab':'IfcSlab','roof':'IfcRoof','sanitary':'IfcSanitaryTerminal'}
OUTDOOR=re.compile(r'balcon|balkon|loggia|terrass|terraz|outdoor|aussen|exterieur|shaft|schacht|gaine|void|luftraum|vide\b',re.I)

def unsupported(reason,status='unsupported'):return {'status':status,'answer':None,'unit':None,'evidence':[],'warnings':[reason],'calculation_trace':[]}
def success(answer,unit,evidence,trace,warnings=None):return {'status':'success','answer':answer,'answer_type':'number' if isinstance(answer,(int,float)) else 'text','unit':unit,'evidence':evidence,'calculation_trace':trace,'warnings':warnings or []}
def count(entities,note):
 evidence=[dict(e,included=True) for e in entities]
 return success(len(evidence),'count',evidence,[{'operation':'count_unique_included_entities','entity_ids':[e['id'] for e in evidence],'value':len(evidence),'note':note}])

def pdf_answer(facts,task,question):
 op,target,filters=task['operation'],task['target'],task['filters']
 if task['scope']=='model':return unsupported('This PDF is a drawing view. Model-wide counts/quantities require an explicitly supplied IFC; no associated model was opened.','abstained')
 if filters.get('schedule'):return pdf_schedule(facts,task,question)
 if len(facts['pages'])>1 and not filters.get('page') and not filters.get('all_pages'):
  return unsupported('Multiple PDF pages are present; specify a page or explicitly ask across all pages.','abstained')
 if filters.get('page') and not 1<=filters['page']<=len(facts['pages']):return unsupported('Requested PDF page does not exist.','abstained')
 rooms=[e for e in facts['entities'] if e['kind']=='room' and (not filters.get('page') or e['page']==filters['page'])];apartments=[e for e in facts['entities'] if e['kind']=='apartment' and (not filters.get('page') or e['page']==filters['page'])]
 if target=='apartment' and op=='count':
  if not apartments:return unsupported('No explicit apartment labels were extracted.','abstained')
  return count(apartments,'Explicit apartment identifiers, not room count or legend rows')
 if target not in ('room','apartment'):return unsupported('Native text does not establish fixture/opening instances. This route supports labelled rooms and printed areas; use raster evidence or an IFC for other quantities.','abstained')
 if not rooms:return unsupported('No reliable numbered room/area registry found.','abstained')
 selected=rooms
 if 'label_aliases'in filters:selected=[e for e in selected if norm(e['label'])in{norm(label)for label in filters['label_aliases']}]
 if 'label' in filters:selected=[e for e in selected if norm(e['label'])==norm(filters['label'])]
 if 'room_number' in filters:selected=[e for e in selected if e['room_number']==filters['room_number']]
 if 'apartment' in filters:
  selected=[e for e in selected if e.get('apartment')==filters['apartment']]
  if not selected:return unsupported('Apartment boundary/room association is unresolved; no area sum was guessed.','abstained')
 if filters.get('indoor_only'):selected=[e for e in selected if not OUTDOOR.search(norm(e['label']))]
 if op=='count':return count(selected,'Unique numbered room records with matching labels; extraction completeness requires review')
 if op=='area':
  if not selected:return unsupported('Requested room was not found among printed labelled area records.','abstained')
  if 'room_number' in filters and len(selected)!=1:return unsupported('Room number occurs on multiple pages; specify the page.','abstained')
  if any(e.get('area_m2') is None for e in selected):return unsupported('Some selected rooms have neither printed area nor a valid polygon/scale; missing area is not zero.','abstained')
  values=[e['area_m2'] for e in selected];value=round(sum(values),6)
  return success(value,'m2',selected,[{'operation':'sum_evidenced_room_areas','terms':[{'entity_id':e['id'],'value':e['area_m2'],'unit':'m2','source':e.get('area_method')} for e in selected],'excluded':'balconies/loggias/terraces/outdoor/shafts/voids' if filters.get('indoor_only') else 'none','value':value}],['Room-label/area and apartment-boundary associations are geometric inferences over native text, not source annotations.'])
 return unsupported('This PDF room route supports count and area only.')

def pdf_schedule(facts,task,question):
 # Explicit table extraction by row coordinates. No scheduled quantity is inferred from geometry.
 q=norm(question);marks=re.findall(r'\bU\d{2}\b|\bU[123]-[LR]{2}\b|\bU1-[LR]H\b',question,re.I)
 marks+=re.findall(r'\btype\s+([A-Z]{2})\b',question)
 marks=list(dict.fromkeys(m.upper() for m in marks))
 if not marks:return unsupported('Schedule query needs an explicit type mark; aggregate schedule semantics are not yet validated.','abstained')
 rows=[]
 for page in facts['pages']:
  for mark in marks:
   import pymupdf
   media=page['unrotated_size'];width,height=media[2]-media[0],media[3]-media[1]
   matrices={0:pymupdf.Matrix(1,0,0,1,0,0),90:pymupdf.Matrix(0,1,-1,0,height,0),180:pymupdf.Matrix(-1,0,0,-1,width,height),270:pymupdf.Matrix(0,-1,1,0,0,width)}
   transform=matrices[page['rotation']]
   words=[dict(w,layout_bbox=list(pymupdf.Rect(w['bbox'])*transform)) for w in page['words']]
   hits=[w for w in words if w['text'].upper()==mark.upper()]
   for hit in hits:
    x,y,x2,y2=hit['layout_bbox'];cy=(y+y2)/2;neighbors=[w for w in words if abs((w['layout_bbox'][1]+w['layout_bbox'][3])/2-cy)<max(4,(y2-y)*.6) and w['layout_bbox'][2]<x and x-w['layout_bbox'][2]<100 and re.fullmatch(r'\d+',w['text'])]
    headers=[w for w in words if norm(w['text'])=='count' and w['layout_bbox'][3]<cy and cy-w['layout_bbox'][3]<500 and abs((w['layout_bbox'][0]+w['layout_bbox'][2])/2-x)<600]
    if headers:
     header=min(headers,key=lambda w:(cy-w['layout_bbox'][3])+abs((w['layout_bbox'][0]+w['layout_bbox'][2])/2-x)*.2);hx=(header['layout_bbox'][0]+header['layout_bbox'][2])/2;tol=max(20,(header['layout_bbox'][2]-header['layout_bbox'][0])/2+12)
     neighbors=[w for w in words if re.fullmatch(r'\d+',w['text']) and abs((w['layout_bbox'][1]+w['layout_bbox'][3])/2-cy)<max(4,(y2-y)*.6) and abs((w['layout_bbox'][0]+w['layout_bbox'][2])/2-hx)<tol]
    if len(neighbors)==1:
     value=int(neighbors[0]['text']);rows.append({'id':f'schedule-{page["page"]}-{mark}-{len(rows)}','kind':'schedule_row','page':page['page'],'bbox':[min(neighbors[0]['bbox'][0],hit['bbox'][0]),min(neighbors[0]['bbox'][1],hit['bbox'][1]),max(neighbors[0]['bbox'][2],hit['bbox'][2]),max(neighbors[0]['bbox'][3],hit['bbox'][3])],'type_mark':mark.upper(),'quantity':value,'text':neighbors[0]['text']+' '+hit['text'],'coordinate_system':'PDF unrotated points','method':'native schedule same-row quantity association'})
 if not rows or len(rows)!=len(set(m.upper() for m in marks)):return unsupported('Schedule mark/quantity association is missing or ambiguous; inspect the table.','abstained')
 if task['operation']!='count':return unsupported('Schedule property columns are not yet validated.','abstained')
 return success(sum(r['quantity'] for r in rows),'count',rows,[{'operation':'sum_explicit_schedule_quantities','terms':[r['quantity'] for r in rows]}],['This is an explicit schedule quantity, not an instance-box count.'])

def raster_answer(facts,task,question):
 if task.get('filters',{}).get('label_aliases'):return unsupported('Corridor-label counting currently requires a PDF numbered-room registry.','unsupported')
 op,target=task['operation'],task['target'];entities=facts['entities'];q=norm(question)
 if task.get('scope')=='model':return unsupported('A raster drawing does not expose the whole associated BIM model; supply an explicit IFC for model-wide quantities.','abstained')
 if task.get('scope')=='floor' or set(task.get('filters',{}))-{'label'}:return unsupported('Requested raster scope/qualifiers are not spatially resolved; no whole-image count was substituted.','abstained')
 if op!='count':return unsupported('Raster physical area/volume/length requires a validated scale or printed numeric evidence; none is assumed.','abstained')
 allowed={'window':('icon','window'),'door':('icon','door'),'toilet_fixture':('icon','toilet_fixture'),'sink':('icon','sink'),'bathtub':('icon','bathtub'),'bedroom':('room','bedroom'),'kitchen':('room','kitchen'),'room':('room',None)}
 if target in allowed and not task['filters'].get('label'):
  kind,cls=allowed[target];selected=[e for e in entities if e['kind']==kind and (e['class']==cls if cls else e['class'] not in ('background','outdoor','undefined'))]
  result=count(selected,'Official reference reconstructed instance polygons; no semantic pixel component counts')
  result['warnings']=['Experimental model instances; omissions and false positives possible. Zero does not verify absence.']
  if target=='door':result['warnings'].append('Counts reconstructed door openings, not proven door leaves; multi-leaf semantics may differ.')
  if target=='sink':result['warnings'].append('Each reconstructed sink polygon is one fixture; double-bowl grouping is not independently verified.')
  return result
 if target in ('sauna','balcony','wc_room','bathroom'):
  patterns={'sauna':r'^(s|sauna)$','balcony':r'^(parv\.?|parveke|balcony|balkon)$','wc_room':r'^wc$','bathroom':r'^(kph|kh|ph|pesuhuone|bathroom)$'}
  selected=[]
  # Labels are associated to reconstructed rooms; repeated text within one room is not another room.
  from shapely.geometry import Point,Polygon
  for room in [e for e in entities if e['kind']=='room' and e['class'] not in ('background','outdoor')]:
   poly=Polygon(room['polygon']);labels=[w for w in facts.get('words',[]) if re.fullmatch(patterns[target],norm(w['text'])) and poly.covers(Point((w['bbox'][0]+w['bbox'][2])/2,(w['bbox'][1]+w['bbox'][3])/2))]
   if labels:selected.append(dict(room,matched_labels=labels))
  if not selected:return unsupported('Required room distinction has no reliably associated OCR label; an icon or generic bath segment is not a room count.','abstained')
  result=count(selected,'OCR label associated with a reference room polygon');result['warnings']=['OCR-label coverage is incomplete; this is an experimental count of evidenced rooms.'];return result
 if target=='shower_bath':return unsupported('The model has bathtub but no shower channel. Combined shower/bath completeness is unsupported.','abstained')
 return unsupported('No validated instance mapping for this raster target.','abstained')

def ifc_answer(facts,task,question):
 op,target,filters=task['operation'],task['target'],task['filters'];entities=facts['entities']
 if filters.get('label_aliases'):return unsupported('Corridor-label counting currently requires a PDF numbered-room registry.','unsupported')
 if target=='software_schema':
  evidence=[{'id':'ifc-header','kind':'ifc_header','schema':facts['schema'],'applications':facts['applications'],'property':'FILE_SCHEMA / IfcApplication'}]
  return success('; '.join([facts['schema']]+[a['name']+' '+a['version'] for a in facts['applications']]),None,evidence,[{'operation':'read_explicit_header_and_IfcApplication'}])
 if target=='material':
  element_cls=IFC_CLASSES.get(filters.get('element_target'))
  rows=[e for e in entities if e.get('materials') and (not element_cls or e['class']==element_cls or e['class']==element_cls+'StandardCase')];names=sorted({n for e in rows for n in e['materials'] if n})
  if not names:return unsupported('No explicit material associations found.','abstained')
  return success(names,None,[{'id':e['id'],'guid':e['guid'],'property':'IfcRelAssociatesMaterial','values':e['materials']} for e in rows],[{'operation':'unique_explicit_material_names'}])
 cls=IFC_CLASSES.get(target)
 if cls is None:return unsupported('This question requires an unregistered IFC classification/property relation.','abstained')
 rows=[e for e in entities if e['class']==cls or (cls=='IfcWall' and e['class']=='IfcWallStandardCase') or (cls=='IfcDoor' and e['class']=='IfcDoorStandardCase') or (cls=='IfcWindow' and e['class']=='IfcWindowStandardCase')]
 if task['scope']=='floor':
  names=sorted({e['name'] for e in entities if e['class']=='IfcBuildingStorey' and e['name']});hint=norm(filters.get('floor_name',''));matched=[n for n in names if hint and hint in norm(n)]
  if not matched:
   storeys=sorted([e for e in entities if e['class']=='IfcBuildingStorey'],key=lambda e:e.get('elevation') or 0)
   mapping={'ground':0,'first':1,'second':2,'third':3,'basement':-1,'top':len(storeys)-1}
   if hint in mapping and storeys:
    ground=next((i for i,e in enumerate(storeys) if e.get('elevation') is not None and e['elevation']>=0),0)
    index=(ground+mapping[hint]) if hint in ('ground','first','second','third') else mapping[hint]
    if hint=='basement':matched=[e['name'] for e in storeys if (e.get('elevation') or 0)<0]
    elif 0<=index<len(storeys):matched=[storeys[index]['name']]
  if len(matched)!=1:return unsupported('Floor name cannot be uniquely mapped to IFC storeys.','abstained')
  rows=[e for e in rows if e.get('floor')==matched[0]]
 if op=='count':
  if re.search(r'residential|external|internal|with |without |excluding|except|versus|how many of each',norm(question)):
   return unsupported('This occurrence count has an unimplemented classification/filter or multi-part scope; a model-wide scalar count would be misleading.','abstained')
  return count([{'id':e['id'],'guid':e['guid'],'class':e['class'],'name':e['name'],'floor':e['floor'],'property':'explicit IFC occurrence'} for e in rows],'Distinct IFC occurrence GUIDs; type definitions excluded')
 if op=='list':
  if not rows:return unsupported('No matching named occurrences found.','abstained')
  return success([e['name'] for e in rows if e['name']],None,[{'id':e['guid'],'guid':e['guid'],'property':'Name','value':e['name']} for e in rows],[{'operation':'list_explicit_occurrence_names'}])
 if op=='property':
  key=filters.get('property')
  if key=='type_breakdown':
   groups={}
   for e in rows:
    typ=e.get('type')
    if not typ:return unsupported('Some selected occurrences lack explicit type relations; no complete type breakdown is asserted.','abstained')
    name=typ.get('name') or typ['guid'];groups.setdefault(name,[]).append(e)
   evidence=[];answer=[]
   for name,members in groups.items():
    thickness=[]
    for e in members:
     for pset,properties in {**e['properties'],**e['quantities']}.items():
      for k,v in properties.items():
       if 'thickness' in norm(k) and isinstance(v,(float,int)) and not isinstance(v,bool):thickness.append(v*facts['unit_scales_to_si']['LENGTHUNIT'])
     evidence.append({'id':e['guid'],'guid':e['guid'],'property':'IsTypedBy / IfcRelDefinesByType','type':e['type']})
    answer.append({'type':name,'count':len(members),'thickness_m':sorted(set(thickness)) if thickness else None})
   return success(answer,None,evidence,[{'operation':'group_explicit_type_relations_and_count_GUIDs'}],['Missing thickness is reported as null, not zero.'])
  selected=[]
  if not key:return unsupported('An explicit supported property name is required.','abstained')
  for e in rows:
   for pset,properties in e['properties'].items():
    for k,v in properties.items():
     if norm(k)==norm(key):selected.append({'id':e['guid'],'guid':e['guid'],'property':pset+'.'+k,'value':v})
  if not selected:return unsupported('Requested property is not explicitly available on selected occurrences.','abstained')
  values=sorted({str(e['value']) for e in selected})
  return success(values[0] if len(values)==1 else values,None,selected,[{'operation':'read_explicit_property_values','property':key}],['Only occurrences carrying the property contribute; missing properties are not inferred.'])
 if op in ('area','volume','length'):
  dimension={'area':'AREAUNIT','volume':'VOLUMEUNIT','length':'LENGTHUNIT'}[op];kind=filters.get('quantity_kind');candidates=[];missing=[]
  policy=facts.get('unit_policy',{})
  if dimension not in policy.get('declared_project_units',[]) or policy.get('explicit_quantity_unit_override_ids'):
   return unsupported('QTO unit dimension is undeclared or uses per-quantity overrides; this route cannot safely normalize it yet.','abstained')
  for e in rows:
   values=[]
   for pset,props in e['quantities'].items():
    for key,value in props.items():
     if key=='id' or not isinstance(value,(int,float)) or isinstance(value,bool):continue
     name=norm(key)
     if op not in name:continue
     if kind and kind not in name:continue
     values.append((pset,key,value))
   if not kind:
    # Do not mix net and gross or choose an arbitrary dimension.
    unqualified=[v for v in values if not any(k in norm(v[1]) for k in ['net','gross'])]
    values=unqualified if unqualified else values
   if len(values)!=1:missing.append(e['guid']);continue
   pset,key,value=values[0];scaled=value*facts['unit_scales_to_si'][dimension];candidates.append({'id':e['guid'],'guid':e['guid'],'property':pset+'.'+key,'raw_value':value,'value_si':scaled,'unit':{'area':'m2','volume':'m3','length':'m'}[op]})
  if missing or not candidates:return unsupported(f'Quantity is missing or ambiguous on {len(missing)} of {len(rows)} selected occurrences; missing QTO is not zero.','abstained')
  return success(sum(e['value_si'] for e in candidates),{'area':'m2','volume':'m3','length':'m'}[op],candidates,[{'operation':'sum_explicit_QTO_in_SI','terms':[{'guid':e['guid'],'property':e['property'],'value':e['value_si']} for e in candidates]}])
 return unsupported('This IFC operation is not registered.','abstained')
