"""Offline benchmark scoring and failure review. Gold never enters the QA package."""
import argparse,collections,importlib.util,json,math,re,statistics,time
from pathlib import Path
from qa.common import ROOT,write_json,sha,norm
from evaluation import numeric as provided
def percentile(values,p):
 if not values:return None
 values=sorted(values);i=(len(values)-1)*p;lo=math.floor(i);hi=math.ceil(i);return values[lo]+(values[hi]-values[lo])*(i-lo)
def fact_tokens(text):
 # Narrow auditable text diagnostic; no LLM judge and no claim of full semantic grading.
 text=norm(text);facts=set(re.findall(r'ifc\s*2x3|ifc\s*4x3|ifc\s*4|revit|archicad|autodesk|allplan|tekla|freecad',text));facts.update(re.findall(r'\d+(?:[.,]\d+)?\s*(?:m2|m3|m²|m³|mm|cm|metres|meters)\b',text));facts.update(re.findall(r'[\'"«]([^\'"»]{2,80})[\'"»]',text));return {f.replace(' ','') for f in facts}
CATEGORY_TARGET={'count_labelled_rooms':'room','count_windows':'window','count_doors':'door','count_sinks':'sink','count_toilet_fixtures':'toilet_fixture','count_toilets':'toilet_fixture','count_storeys':'storey','count_saunas':'sauna','count_kitchens':'kitchen','count_bedrooms':'bedroom','count_bathrooms':'bathroom','count_separate_wc_rooms':'wc_room','count_showers_and_baths':'shower_bath','count_balconies':'balcony','count_apartments':'apartment','count_spaces':'room','count_walls':'wall','count_stairs':'stair','area_room':'room','area_apartment':'apartment'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--answers',type=Path,required=True);p.add_argument('--predictions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Preserve scored reports; choose a new output')
 gold=[json.loads(l) for l in a.answers.open()];preds=[json.loads(l) for l in a.predictions.open()];lookup={r['sample_id']:r for r in preds}
 if len(lookup)!=len(preds) or len({g['sample_id'] for g in gold})!=len(gold):raise ValueError('Duplicate sample IDs')
 if set(lookup)-{g['sample_id'] for g in gold}:raise ValueError('Predictions outside this benchmark')
 buckets=collections.defaultdict(list);records=[];fact_grades=[];op_matches=[];target_matches=[]
 for g in gold:
  pred=lookup.get(g['sample_id']);grade=provided.score(g,pred);typ=g['type'];record={'sample_id':g['sample_id'],'question':g['question'],'path':g['path'],'expected':g['answer'],'expected_unit':g['unit'],'type':typ,'category':g.get('category'),'source':g.get('source'),'language':g.get('language'),'format':Path(g['path']).suffix,'status':pred.get('status','missing') if pred else 'missing','answer':pred.get('answer') if pred else None,'unit':pred.get('unit') if pred else None,'route':pred.get('route','missing') if pred else 'missing',**grade}
  if pred:
   record['timing']=pred.get('timing',{});record['evidence_count']=len(pred.get('evidence',[]));record['warnings']=pred.get('warnings',[]);record['peak_gpu_memory_bytes']=pred.get('peak_gpu_memory_bytes')
   op=pred.get('task',{}).get('operation');record['operation_taxonomy_match']=op==typ if typ in ('count','area','volume','length') else None
   if record['operation_taxonomy_match'] is not None:op_matches.append(record['operation_taxonomy_match'])
   expected_target=CATEGORY_TARGET.get(g.get('category'));record['target_taxonomy_match']=pred.get('task',{}).get('target')==expected_target if expected_target else None
   if record['target_taxonomy_match'] is not None:target_matches.append(record['target_taxonomy_match'])
   if typ=='text' and pred['status']=='success':
    expected_facts=fact_tokens(g['answer']);proposed=fact_tokens(pred['answer'])
    if expected_facts:
     common=expected_facts&proposed;record['text_fact_diagnostic']={'reference_facts':sorted(expected_facts),'answer_facts':sorted(proposed),'precision':len(common)/len(proposed) if proposed else 0,'recall':len(common)/len(expected_facts),'not_official_semantic_grade':True};fact_grades.append(record['text_fact_diagnostic'])
  records.append(record)
  for key in ['all','type:'+typ,'category:'+str(g.get('category')),'source:'+str(g.get('source')),'format:'+record['format'],'language:'+str(g.get('language'))]:buckets[key].append(record)
 def summarize(rs):
  numeric=[r for r in rs if r['type'] in ('count','area','length','volume')];valid=[r for r in rs if r['type']=='count' and 'absolute_error' in r];success=[r for r in rs if r['status']=='success'];lat=[r.get('timing',{}).get('total_seconds') for r in rs if r.get('timing',{}).get('total_seconds') is not None]
  return {'total':len(rs),'numeric_total':len(numeric),'numeric_passed':sum(r['passed'] is True for r in numeric),'numeric_accuracy':sum(r['passed'] is True for r in numeric)/len(numeric) if numeric else None,'coverage':len(success)/len(rs),'statuses':dict(collections.Counter(r['status'] for r in rs)),'count_mae':statistics.mean(r['absolute_error'] for r in valid) if valid else None,'count_mae_denominator':len(valid),'signed_count_bias':statistics.mean(r['signed_error'] for r in valid) if valid else None,'count_exact_valid_outputs':sum(r['absolute_error']==0 for r in valid)/len(valid) if valid else None,'evidence_success_n':sum(r.get('evidence_count',0)>0 for r in success),'evidence_success_denominator':len(success),'latency_p50_seconds':percentile(lat,.5),'latency_p95_seconds':percentile(lat,.95),'reasons':dict(collections.Counter(r['reason'] for r in rs))}
 allsummary=summarize(records);timings={}
 for name,rs in [('first_file',[r for r in records if not r.get('timing',{}).get('cache_hit',True)]),('cached_query',[r for r in records if r.get('timing',{}).get('cache_hit')]),('cold_model',[r for r in records if r.get('timing',{}).get('cold_model')])]:
  timings[name]={'n':len(rs),'p50_total_seconds':percentile([r['timing']['total_seconds'] for r in rs],.5),'p95_total_seconds':percentile([r['timing']['total_seconds'] for r in rs],.95),'parse_seconds_sum':sum(r['timing'].get('first_file_parse_seconds',0) for r in rs),'model_loading_seconds_sum':sum(r['timing'].get('model_loading_seconds',0) for r in rs),'inference_seconds_sum':sum(r['timing'].get('inference_seconds',0) for r in rs)}
 report={'label':a.label,'summary':allsummary,'by_group':{k:summarize(rs) for k,rs in buckets.items() if k!='all'},'timings':timings,'routing_diagnostic':{'operation_taxonomy_agreement':statistics.mean(op_matches) if op_matches else None,'operation_n':len(op_matches),'target_taxonomy_agreement':statistics.mean(target_matches) if target_matches else None,'target_n':len(target_matches),'note':'Gold categories are supplied heuristic metadata; this is a routing diagnostic separate from numeric answer scores, not verified semantic routing accuracy.'},'text_fact_diagnostic':{'scored_n':len(fact_grades),'mean_precision':statistics.mean(x['precision'] for x in fact_grades) if fact_grades else None,'mean_recall':statistics.mean(x['recall'] for x in fact_grades) if fact_grades else None,'rubric':'Exact schema/software names, explicitly quoted entities, and unit-bearing numeric facts; no normalized prose score or model judge. Uncovered narrative semantics require human review. No official combined score.'},'peak_gpu_memory_bytes':max((r['peak_gpu_memory_bytes'] for r in records if r.get('peak_gpu_memory_bytes') is not None),default=None),'predictions_sha256':sha(a.predictions),'answers_sha256':sha(a.answers),'samples':records,'note':'Count exact; area/length/volume <=2% relative error; zero references use absolute tolerance 1e-9. All numeric rows, including abstained/unsupported/failed/missing, remain in the accuracy denominator. Text diagnostics are not an official semantic grade. Pretrained overlap unknown; quick/smoke are development.'}
 write_json(a.output,report);print(json.dumps(allsummary,indent=2))
 gallery=ROOT/'results/qa-gallery.json';existing=json.loads(gallery.read_text()) if gallery.exists() else {'reports':[]}
 # The web gallery has bounded representative successes/failures; full per-row scores remain in report.json.
 sample=sorted(records,key=lambda r:(r['passed'] is True,r['sample_id']))[:100]
 existing['reports']=[r for r in existing['reports'] if r['label']!=a.label]+[{'label':a.label,'summary':allsummary,'samples':sample,'note':report['note']}];write_json(gallery,existing)
if __name__=='__main__':main()
