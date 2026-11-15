"""Development-selected postprocessing of unchanged real RT-DETR predictions.
Raw model cache remains immutable and author settings remain recorded.
"""
from .structural import answer as original_answer,parse,SETTINGS
from v3.dedup import suppress
PROFILE={'door':'conf65_fragments85','window':'conf50_fragments85'}
def answer(file,task):
 result=original_answer(file,task);raw=parse(file);entities,removed=suppress(raw['entities'],PROFILE[task['target']]);selected=[e for e in entities if e['class']==task['target']]
 result.update(answer=len(selected),evidence=selected,route='raster.rtdetr-l.v3',raw_prediction={'answer':result['answer'],'evidence':result['evidence']},postprocessing={'version':'v3-grid-selected','profile':PROFILE[task['target']],'selection':'quick development only; possible pretrained overlap','removed':[x for x in removed if x['entity']['class']==task['target']]},calculation_trace=[{'operation':'count_unique_included_entities','ids':[e['id'] for e in selected],'value':len(selected)}])
 result['warnings'].append('Development-selected score/overlap filtering can remove true adjacent instances; original detector outputs retained.')
 return result
