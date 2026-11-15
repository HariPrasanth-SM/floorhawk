"""Offline-only paired evaluation: all IDs, regressions, rescues and stage timings."""
import argparse,json,statistics,collections
from pathlib import Path
from qa.common import write_json,sha
from qa_score import provided,percentile

def score(answers,local,hybrid,output,no_ocr=None,baseline=None):
 gold=[json.loads(l) for l in answers.open()]
 def load(path):return {r['sample_id']:r for r in map(json.loads,path.open())} if path and path.exists() else {}
 modes={'A1':load(local),'A2':load(hybrid)}
 if no_ocr:modes['A1_no_OCR']=load(no_ocr)
 if baseline:modes['A0']=load(baseline)
 reports={};scores={}
 for mode,preds in modes.items():
  if set(preds)!={g['sample_id'] for g in gold}:raise ValueError('Every paired mode must have exactly all frozen IDs')
  graded=[]
  for g in gold:
   p=preds[g['sample_id']];s=provided.score(g,p);graded.append(dict(sample_id=g['sample_id'],type=g['type'],category=g.get('category'),source=g.get('source'),language=g.get('language'),format=Path(g['path']).suffix,status=p['status'],route=p['route'],answer=p['answer'],expected=g['answer'],**s))
  scores[mode]={r['sample_id']:r for r in graded}
  def summary(rs):
   numeric=[r for r in rs if r['type'] in ('count','area','length','volume')];counts=[r for r in rs if r['type']=='count'];valid=[r for r in counts if 'absolute_error' in r];categories=collections.defaultdict(list)
   for r in numeric:categories[r['category']].append(r['passed'] is True)
   return {'n':len(rs),'numeric_n':len(numeric),'numeric_passed':sum(r['passed'] is True for r in numeric),'micro_numeric_accuracy':sum(r['passed'] is True for r in numeric)/len(numeric) if numeric else None,'macro_category_numeric_accuracy':statistics.mean(statistics.mean(x) for x in categories.values()) if categories else None,'count_n':len(counts),'count_exact_all':sum(r['passed'] is True for r in counts)/len(counts) if counts else None,'count_mae_valid':statistics.mean(r['absolute_error'] for r in valid) if valid else None,'count_bias_valid':statistics.mean(r['signed_error'] for r in valid) if valid else None,'count_within_one_valid':statistics.mean(r['absolute_error']<=1 for r in valid) if valid else None,'count_valid_n':len(valid),'count_within_one_all':sum(r['absolute_error']<=1 for r in valid)/len(counts) if counts else None,'statuses':dict(collections.Counter(r['status'] for r in rs)),'coverage':sum(r['status']=='success' for r in rs)/len(rs),'execution_failure_rate':sum(r['status']=='failed' for r in rs)/len(rs),'text_ungraded_n':sum(r['type']=='text' for r in rs)}
  groups={}
  for field in ('category','source','language','format','type','route'):
   for value in {r[field] for r in graded}:groups[field+':'+str(value)]=summary([r for r in graded if r[field]==value])
  lat=[p['timing']['total_seconds'] for p in preds.values()];stages=collections.defaultdict(list)
  for p in preds.values():
   for name,t in p.get('stage_timings',{}).items():
    if isinstance(t,dict):stages[name].append(t)
  reports[mode]={'summary':summary(graded),'by_group':groups,'latency':{'p50_seconds':percentile(lat,.5),'p95_seconds':percentile(lat,.95),'sum_question_seconds':sum(lat),'note':'Shared warmed fact caches. Stage cold/warm flags and original extraction cost retained; not neural throughput.'},'stage_records':dict(stages),'samples':graded,'predictions_sha256':sha({'A1':local,'A2':hybrid,'A1_no_OCR':no_ocr,'A0':baseline}[mode])}
 changes=collections.Counter({k:0 for k in ('rescued','unchanged_correct','correct_to_incorrect','still_wrong')});changes_ids=collections.defaultdict(list)
 for g in gold:
  if g['type']=='text':continue
  sid=g['sample_id'];a=scores['A1'][sid]['passed'] is True;b=scores['A2'][sid]['passed'] is True;label='unchanged_correct' if a and b else 'correct_to_incorrect' if a else 'rescued' if b else 'still_wrong';changes[label]+=1;changes_ids[label].append(sid)
 calls=sum(p.get('cloud',{}).get('requests',0) for p in modes['A2'].values() if isinstance(p.get('cloud',{}).get('requests',0),int));cost=sum(p.get('cloud',{}).get('estimated_usd_reserved',0) for p in modes['A2'].values());attributed_cost=sum(p.get('cloud',{}).get('original_generation',{}).get('reserved_usd',0) for p in modes['A2'].values());rescued=changes['rescued'];net=rescued-changes['correct_to_incorrect']
 report={'label':'Frozen40 quick-development paired; broad strata, not prevalence-weighted/held-out','sample_ids':[g['sample_id'] for g in gold],'answers_sha256':sha(answers),'modes':reports,'a1_to_a2_numeric_changes':dict(changes),'change_ids':dict(changes_ids),'cloud':{'new_http_requests_reported_by_results':calls,'call_rate':calls/len(gold),'reserved_estimated_usd':cost,'original_generation_questions':sum(bool(p.get('cloud',{}).get('original_generation')) for p in modes['A2'].values()),'original_generation_question_rate':sum(bool(p.get('cloud',{}).get('original_generation')) for p in modes['A2'].values())/len(gold),'attributed_original_generation_reserved_usd':attributed_cost,'attributed_reserved_cost_per_additional_correct_net':attributed_cost/net if net>0 else None,'note':'Cache hits keep original generation usage separately; global ledger also includes setup/failed earlier versions. Provider bill not guaranteed.'},'text_rubric':'Unknown prose semantics remain ungraded. Supplied numeric scorer only; no self-judging or invented combined score.','localization':'No compatible spatial reference supplied: no precision/recall/mAP/IoU claim','intervals':'No translated-question IID confidence intervals; no group bootstrap implemented'}
 if output.exists():raise ValueError('Preserve reports; new output required')
 write_json(output,report);print(json.dumps({'modes':{k:v['summary'] for k,v in reports.items()},'changes':dict(changes),'cloud':report['cloud']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--answers',type=Path,required=True);p.add_argument('--local',type=Path,required=True);p.add_argument('--hybrid',type=Path,required=True);p.add_argument('--no-ocr',type=Path);p.add_argument('--baseline',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();score(a.answers,a.local,a.hybrid,a.output,a.no_ocr,a.baseline)
