"""Question-only deterministic templates. Gold type/category/unit are never input."""
import re
from .common import norm
OPERATIONS={'count','area','volume','length','property','list','unknown'}
TARGETS={'window','door','toilet_fixture','sink','shower_bath','shower','bathtub','sauna','bedroom','kitchen','bathroom','wc_room','balcony','apartment','room','wall','stair','storey','building','column','beam','slab','roof','sanitary','software_schema','material','schedule','unknown'}

def validate_task(task):
 if not isinstance(task,dict) or set(task)-{'operation','target','filters','scope','requested_unit','required_evidence','router'}:raise ValueError('Invalid task fields')
 if task.get('operation') not in OPERATIONS or task.get('target') not in TARGETS:raise ValueError('Unregistered operation or target')
 if not isinstance(task.get('filters',{}),dict) or task.get('scope') not in ('drawing','model','floor'):raise ValueError('Invalid task scope/filters')
 return task

def route(question):
 q=norm(question);filters={};operation='unknown';target='unknown'
 if re.search(r'how many|kuinka monta|wie viele|combien|quanti|quante|hoeveel|mitu |hvor mange|ile |what is the (?:total )?number of|wat is het (?:totale )?aantal|qual e il numero|quale.*numero|numero (?:totale )?di',q):operation='count'
 if re.search(r'area|nettoflache|nettowohnflache|nettogeschossflache|surface|flache|pinta-ala|superficie|oppervlakte',q):operation='area'
 if re.search(r'volume|tilavuus|volumen',q):operation='volume'
 if re.search(r'total length|length of|gesamtlange|longueur|pituus|lengte',q):operation='length'
 # Quoted room labels can contain apostrophes (Cage d'escalier), so use matching outer delimiters.
 label=re.search(r"(?:labelled|labeled|bezeichnung|designation|designees|denominati|denominate|bezeichnet)\s*[«'\"]\s*(.+?)\s*[»'\"](?:\s+(?:are|on|in|y |gibt|auf|il)|[?.]|$)",q)
 if label:target='room';filters['label']=label[1].strip()
 roomid=re.search(r'(?:room|raum|piece|stanza|locale|huone)\s+([a-z]?\d{1,2}\.\d{2})',q)
 if roomid:target='room';filters['room_number']=roomid[1].upper()
 apartment=re.search(r'(?:apartment|wohnung|appartement|appartamento)\s+([a-z])\b',q)
 if apartment:target='apartment';filters['apartment']=apartment[1].upper()
 if target=='unknown' and re.search(r'labelled|labeled|bezeichnung|designation|denominazione|denominati|denominate|designees',q):
  if '«' in q and '»' in q:filters['label']=q.split('«',1)[1].split('»',1)[0].strip();target='room'
  elif "'" in q:
   parts=q.split("'");filters['label']="'".join(parts[1:-1]).strip();target='room'
 named_room=re.search(r"(?:room|ruimte|raum|stanza|locale)\s+['\"«](.+?)\s*\((\d+)\)['\"»]",q)
 if named_room:target='room';filters.update(label=named_room[1].strip(),room_number=named_room[2])
 if operation=='area' and re.search(r'numbered indoor|nummerierten innenraume|pieces interieures|locali interni',q):target='room';filters['indoor_only']=True
 if target=='unknown':
  patterns=[('software_schema',r'modelling program|modeling program|software|ifc (?:standard|schema)|welche.*programm'),('wc_room',r'separate wc|erillista wc'),('shower_bath',r'showers?.*(?:bathtubs?|baths?)|suihku.*kylpyam'),('toilet_fixture',r'toilet bowls?|wc-istuin|wc-istuim|toilets? \(wc\)|\bwcs\b'),('sink',r'sinks?|washbasin|lavabo|pesu- ja tisk|pesuall'),('window',r'windows?|ikkun|fenster|fenetre|finestr|akna|ramen|vindue'),('door',r'doors?|ovea|oviauk|turen|portes?|deuren|dore'),('storey',r'storeys?|kerrosta|geschosse|verdiepingen|floors \(storeys\)'),('sauna',r'sauna'),('bedroom',r'bedrooms?|makuuhuon'),('kitchen',r'kitchens?|keittio'),('bathroom',r'bathroom|washroom|kylpy- tai pesuhuon'),('balcony',r'balcon|parveke'),('apartment',r'apartments?|wohnungen|appartements?|appartament|logements'),('toilet_fixture',r'toilets?|\bwc\b'),('shower',r'showers?|duschen|douches?|suihku'),('bathtub',r'bathtubs?|badewann|baignoir|kylpyamm'),('wall',r'walls?|wande|wanden|\bmuri\b'),('stair',r'stairs?|treppen'),('column',r'columns?|kolommen'),('beam',r'beams?|balken'),('sanitary',r'sanitary fixtures|sanitaire'),('slab',r'slabs?|decken'),('roof',r'roofs?|daken'),('building',r'buildings?|gebaude|batiments|edifici'),('room',r'rooms?|spaces?|raume|ruimtes?|stanze|locali|spazi|numbered indoor|innenraume|pieces interieures')]
  if operation=='count':patterns.insert(len(patterns)-1,('room',r'\bcorridors?\b|\bkorridore?\b'))
  focus=q
  if operation=='count':
   focus=re.split(r'[\(\[]',q,maxsplit=1)[0]
   lead=re.search(r'(?:how many|kuinka monta|wie viele|hoeveel|quanti|quante|combien(?: de)?|mitu|hvor mange|ile)\s+(.+)',focus)
   if lead:focus=lead[1]
   focus=re.split(r'\b(?:are|is|sind|werden|sono|drawn|shown)\b',focus,maxsplit=1)[0]
  for text in (focus,q):
   for name,pattern in patterns:
    if re.search(pattern,text):target=name;break
   if target!='unknown':break
 if operation=='count'and target=='room'and not filters.get('label')and not filters.get('room_number')and re.search(r'\bcorridors?\b|\bkorridore?\b',q):filters['label_aliases']=['corridor','corridors','korridor','korridore']
 if re.search(r'types.*(?:how many|thickness)|how many of each|broken down by type',q):operation='property';filters['property']='type_breakdown';filters['include_thickness']='thickness' in q
 if re.search(r'fire rating|feuerwiderstand',q):operation='property';filters['property']='FireRating'
 prop=re.search(r'(?:property|eigenschaft)\s+["«]([^"»]+)["»]',q)
 if prop:operation='property';filters['property']=prop[1]
 if operation=='unknown' and re.search(r'what are the names|list (?:the )?(?:names|storeys|floors)|which storeys',q):operation='list'
 page=re.search(r'\b(?:page|seite|pagina)\s+(\d+)\b',q)
 if page:filters['page']=int(page[1])
 if re.search(r'across all pages|all pages|toutes les pages',q):filters['all_pages']=True
 if re.search(r'\bscheduled|schedule|type mark|sheet a\d',q):filters['schedule']=True
 if target=='software_schema':operation='property'
 if re.search(r'materials?|materiaux|baustoff',q):
  filters['element_target']=target if target!='unknown' else None;operation='property';target='material'
 if target=='room' and operation=='area' and 'room_number' not in filters and 'label' not in filters:filters['indoor_only']=True
 if target=='apartment' and operation=='area':filters['indoor_only']=True
 if operation in ('area','volume','length') and re.search(r'\bnet\b|\bnetto\w*|\bnette\b',q):filters['quantity_kind']='net'
 if operation in ('area','volume','length') and re.search(r'gross (?:area|volume)|\bbrutto\w*|\bbrute\b',q):filters['quantity_kind']='gross'
 scope='model' if re.search(r'in the model|in this ifc|in this model|in het model|im modell|modele|nel modello|del modello',q) else 'drawing'
 floor=re.search(r'(?:on|in|of) (?:the )?(ground|first|second|third|basement|top|\d+)(?: floor| storey)',q)
 if floor:scope='floor';filters['floor_name']=floor[1]
 requested={'count':'count','area':'m2','volume':'m3','length':'m','property':None,'list':None,'unknown':None}[operation]
 if re.search(r'\bcm\b',q):requested='cm'
 if re.search(r'\bmm\b',q):requested='mm'
 return validate_task({'operation':operation,'target':target,'filters':filters,'scope':scope,'requested_unit':requested,'required_evidence':['source references','entity instances' if operation=='count' else 'printed value or explicit IFC quantity'],'router':'deterministic templates v2'})
