"""Native table prefix filtering and explicit opening/leaf quantity arithmetic.
Reuses the existing strict mark/Count-column association. No model-wide inference
or geometric door count is substituted for a schedule quantity.
"""
import re
from qa.common import norm,bbox_union
from qa.tools import pdf_schedule,success,unsupported

def answer(facts,task,question):
 if task.get('operation')!='count' or task.get('target')!='door' or not task.get('filters',{}).get('schedule'):return None
 prefix=re.search(r"(?:description|descriptions?).*?starts? with\s*['\"«]([^'\"»]+)['\"»]",question,re.I)
 if not prefix:return None
 prefix=prefix[1].strip();leaves=bool(re.search(r'\b(?:door )?leaves\b|door leaf',question,re.I));matched={};diagnostics=[]
 import pymupdf
 for page in facts['pages']:
  media=page['unrotated_size'];width,height=media[2]-media[0],media[3]-media[1];matrices={0:pymupdf.Matrix(1,0,0,1,0,0),90:pymupdf.Matrix(0,1,-1,0,height,0),180:pymupdf.Matrix(-1,0,0,-1,width,height),270:pymupdf.Matrix(0,-1,1,0,0,width)};matrix=matrices[page['rotation']];words=[dict(w,layout=list(pymupdf.Rect(w['bbox'])*matrix)) for w in page['words']];headers=[w for w in words if norm(w['text'])=='count']
  for hit in [w for w in words if norm(w['text']).startswith(norm(prefix))]:
   b=hit['layout'];cy=(b[1]+b[3])/2;row=[w for w in words if abs((w['layout'][1]+w['layout'][3])/2-cy)<max(4,(b[3]-b[1])*.6)];marks=[w for w in row if re.fullmatch(r'U\d{2}|U[123]-[LR]{2}|U1-[LR]H',w['text'],re.I) and w['layout'][2]<b[0] and b[0]-w['layout'][2]<200]
   if not marks:continue
   mark=min(marks,key=lambda w:b[0]-w['layout'][2]);mb=mark['layout'];count_headers=[h for h in headers if h['layout'][3]<cy and cy-h['layout'][3]<500 and 0<mb[0]-(h['layout'][0]+h['layout'][2])/2<100]
   if not count_headers:continue  # Do not include the per-instance Number table.
   widths=[w for w in words if norm(w['text'])=='width' and w['layout'][3]<cy and cy-w['layout'][3]<500 and w['layout'][0]>b[0] and w['layout'][0]-b[0]<600]
   if not widths:return unsupported('Description-column boundary is ambiguous; inspect the native schedule.','abstained')
   boundary=min(widths,key=lambda w:w['layout'][0]-b[0])['layout'][0]-2;description_words=sorted([w for w in row if w['layout'][0]>=b[0]-1 and w['layout'][2]<boundary],key=lambda w:w['layout'][0]);description=' '.join(w['text'] for w in description_words)
   if not norm(description).startswith(norm(prefix)):continue
   key=(page['page'],mark['text'].upper())
   if key in matched:return unsupported('Repeated type rows make prefix aggregation ambiguous.','abstained')
   matched[key]={'mark':mark['text'].upper(),'description':description,'description_bbox':bbox_union([w['bbox'] for w in description_words])}
 if not matched:return unsupported('No unambiguous type-table rows match the requested description prefix.','abstained')
 evidence=[];terms=[]
 for (page,mark),item in matched.items():
  subset=dict(facts,pages=[p for p in facts['pages'] if p['page']==page]);result=pdf_schedule(subset,dict(task,filters={'schedule':True}),f'How many doors of type {mark} are scheduled?')
  if result['status']!='success' or len(result['evidence'])!=1:return unsupported('A matching type has ambiguous/missing Count-column quantity: '+mark,'abstained')
  e=dict(result['evidence'][0]);description=item['description'];multiplier=2 if leaves and re.search(r'\bDOUBLE\b|\bPAIR\b|2[- ]LEAF',description,re.I) else 1
  e.update(description=description,opening_quantity=e['quantity'],leaf_multiplier=multiplier,leaf_quantity=e['quantity']*multiplier);e['bbox']=bbox_union([e['bbox'],item['description_bbox']]);e['quantity']=e['leaf_quantity'] if leaves else e['opening_quantity'];evidence.append(e);terms.append({'type_mark':mark,'opening_quantity':e['opening_quantity'],'leaf_multiplier':multiplier,'value':e['quantity'],'description':description})
 r=success(sum(e['quantity'] for e in evidence),'count',evidence,[{'operation':'sum_explicit_schedule_leaf_quantities' if leaves else 'sum_explicit_schedule_quantities','description_prefix':prefix,'terms':terms}],['Explicit schedule quantities are separate from drawing instance-box counts.','For requested leaves, explicit DOUBLE/PAIR type descriptions contribute two leaves per scheduled opening; other matched types contribute one.']);r.update(route='pdf.native-schedule-prefix.v3',schedule_filter={'description_prefix':prefix,'quantity_semantics':'door_leaves' if leaves else 'scheduled_openings'});return r
