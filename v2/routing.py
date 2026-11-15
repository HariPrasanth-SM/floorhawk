"""Reject generated filter fields the deterministic executors would ignore."""
from qa.router import validate_task
ALLOWED={'label':str,'room_number':str,'apartment':str,'page':int,'all_pages':bool,'schedule':bool,'floor_name':str,'indoor_only':bool,'quantity_kind':str,'property':str,'element_target':str,'include_thickness':bool}
def validate_routed(task):
 t=validate_task(task);filters=t.get('filters',{})
 if any(k not in ALLOWED or not isinstance(v,ALLOWED[k]) or isinstance(v,(dict,list)) for k,v in filters.items()):raise ValueError('Generated filters cannot be executed without loss')
 unit=t.get('requested_unit');t['requested_unit']=None if unit=='null' else unit
 if t['requested_unit'] not in ('count','m','m2','m3','mm','cm',None):raise ValueError('Unregistered unit')
 if not isinstance(t.get('required_evidence',[]),list) or any(not isinstance(x,str) or len(x)>500 for x in t.get('required_evidence',[])):raise ValueError('Invalid evidence requirements')
 return t
