"""Trusted crop-OCR adapter, sharing the existing PP-OCR model and room geometry."""
from v3.ocr import candidates,PATTERNS
def answer(file,task,facts):
 target=task.get('target')
 if task.get('operation')!='count' or target not in PATTERNS or task.get('filters'):return None
 result=candidates(file,facts);selected=result['results'][target];ocr=result['ocr']
 if selected['ambiguous'] or not selected['entities']:return {'ocr_diagnostic':{'matched_rooms':len(selected['entities']),'ambiguous_labels':selected['ambiguous'],'timing':ocr['timing'],'cache_hit':ocr['cache_hit']}}
 entities=selected['entities']
 return {'status':'success','answer':len(entities),'unit':'count','evidence':entities,'route':'raster.ppocr-crops-room-association.v3','ocr_timing':dict(ocr['timing'],cache_hit=ocr['cache_hit']),'ocr_settings':ocr['settings'],'warnings':['Unique OCR-label containment is a model hypothesis; missed labels/segmentation errors remain possible.','Recognizer scores are not probabilities. Outdoor room geometry is included for explicit balcony labels.'],'calculation_trace':[{'operation':'count_unique_included_entities','ids':[e['id'] for e in entities],'value':len(entities)}]}
