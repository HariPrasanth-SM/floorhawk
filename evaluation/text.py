"""Conservative development text rubric v1, frozen before candidate scoring.
No substring credit, model judge, reference-dependent alias generation or free-form guesses.
"""
import unicodedata,re,json
VERSION='text-rubric-1'
ALIASES={'ifc2x_final':'ifc2x final','ifc2x3':'ifc2x3','ifc 2x3':'ifc2x3','ifc4':'ifc4','ifc 4':'ifc4','ifc4x3':'ifc4x3','ifc 4.3':'ifc4x3'}
def normalize(v):
 if not isinstance(v,str):raise ValueError('Text scalar required')
 text=' '.join(unicodedata.normalize('NFKC',v).casefold().split()).strip().rstrip('.')
 return ALIASES.get(text,text)
def score(reference,prediction,rule='free_form'):
 if prediction is None:return {'graded':False,'reason':'no_answer','version':VERSION}
 if rule=='scalar':
  if not isinstance(reference,str)or not isinstance(prediction,str):return {'graded':False,'reason':'unsupported_scalar_schema','version':VERSION}
  equal=normalize(reference)==normalize(prediction);return {'graded':True,'passed':equal,'reason':'normalized_exact_or_explicit_alias','version':VERSION}
 if rule=='set':
  if not isinstance(reference,list)or not isinstance(prediction,list)or any(not isinstance(v,str)for v in reference+prediction):return {'graded':False,'reason':'explicit_list_schema_required','version':VERSION}
  a,b={normalize(x)for x in reference},{normalize(x)for x in prediction};tp=len(a&b);precision=tp/len(b)if b else 1 if not a else 0;recall=tp/len(a)if a else 1;f1=2*precision*recall/(precision+recall)if precision+recall else 0;return {'graded':True,'passed':a==b,'precision':precision,'recall':recall,'f1':f1,'exact_set':a==b,'reason':'explicit_set_exact_no_extra_items','version':VERSION}
 return {'graded':False,'passed':None,'reason':'unsupported_free_form_semantics','version':VERSION}
def rule_for(question,reference):
 # Supplied narrative references are not silently parsed into answers.
 if isinstance(reference,list)and all(isinstance(v,str)for v in reference)and re.search(r'\blist\b|\bnames\b|which materials',question,re.I)and not re.search(r'order|sequence|rank|highest|lowest|per floor',question,re.I):return 'set'
 if isinstance(reference,str)and re.fullmatch(r'IFC\s*\d(?:[Xx.]\d)?(?:_FINAL)?',reference.strip()):return 'scalar'
 return 'free_form'
