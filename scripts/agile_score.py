"""Offline three-mode diagnostic scoring; never imported by inference routes."""
import argparse, collections, json, math, statistics, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT
from evaluation import numeric,text
MODES=('local','custom','hybrid')
NUMERIC=('count','area','length','volume')

def read_rows(path):
 return [json.loads(l)for l in path.read_text().splitlines()if l.strip()]

def classify(g,p):
 if p is None:return {'recorded':False,'status':None,'answer':None,'answered':False,'outcome':'Not recorded','numeric_grade':numeric.score(g,None),'text_grade':{}}
 status=p.get('status','invalid_status');answer=p.get('answer');answered=status=='success'and answer is not None
 grade=numeric.score(g,p);tg=text.score(g['answer'],answer,text.rule_for(g['question'],g['answer']))if g['type']=='text'and answered else{}
 if answered:
  if g['type']=='text':outcome=('Text correct'if tg.get('passed')else'Text incorrect')if tg.get('graded')else'Answered but ungraded'
  else:outcome='Correct'if grade['passed']is True else'Incorrect'if grade['passed']is False else'Answered but ungraded'
 else:outcome={'abstained':'Abstained','unsupported':'Unsupported','provider_error':'Provider error','validation_error':'Validation error','blocked':'Blocked'}.get(status,'Execution error')
 return {'recorded':True,'status':status,'answer':answer,'unit':p.get('unit'),'answered':answered,'outcome':outcome,'numeric_grade':grade,'text_grade':tg}

def summary(rows,mode):
 xs=[r[mode]for r in rows];counts=collections.Counter(x['outcome']for x in xs);nr=[r for r in rows if r['type']in NUMERIC];ng=[r for r in nr if r[mode]['answered']and r[mode]['numeric_grade'].get('passed')is not None];tx=[r for r in rows if r['type']=='text'];tg=[r for r in tx if r[mode]['text_grade'].get('graded')];errors=[r[mode]['numeric_grade']for r in nr if r['type']=='count'and 'signed_error'in r[mode]['numeric_grade']]
 ratio=lambda n,d:n/d if d else None
 return {'total':len(rows),'unique_drawing_groups':len({r['drawing_id']for r in rows}),'recorded':sum(x['recorded']for x in xs),'answered':sum(x['answered']for x in xs),'outcomes':dict(counts),'answer_coverage':ratio(sum(x['answered']for x in xs),len(rows)),'numeric_n':len(nr),'numeric_correct':counts['Correct'],'numeric_correct_all':ratio(counts['Correct'],len(nr)),'numeric_graded_answered_n':len(ng),'numeric_correct_graded_answered':ratio(counts['Correct'],len(ng)),'text_n':len(tx),'text_graded_n':len(tg),'text_correct':counts['Text correct'],'text_incorrect':counts['Text incorrect'],'text_ungraded_answered':counts['Answered but ungraded'],'text_correct_graded':ratio(counts['Text correct'],len(tg)),'count_valid_outputs_n':len(errors),'count_mae':statistics.mean(e['absolute_error']for e in errors)if errors else None,'count_signed_bias':statistics.mean(e['signed_error']for e in errors)if errors else None,'under_count':sum(e['signed_error']<0 for e in errors),'over_count':sum(e['signed_error']>0 for e in errors),'exact_count':sum(e['signed_error']==0 for e in errors)}

def paired(rows,a,b):
 numeric_rows=[r for r in rows if r['type']in NUMERIC];matched=[r for r in numeric_rows if r[a]['recorded']and r[b]['recorded']];states=collections.Counter();ids=collections.defaultdict(list)
 for r in matched:
  x,y=r[a]['outcome']=='Correct',r[b]['outcome']=='Correct';state='unchanged_correct'if x and y else'rescue'if y else'regression'if x else'unresolved_or_wrong';states[state]+=1;ids[state].append(r['sample_id'])
 return {'comparison':a+' -> '+b,'numeric_manifest_n':len(numeric_rows),'numeric_recorded_in_both_n':len(matched),'missing_either_n':len(numeric_rows)-len(matched),'states':dict(states),'ids':dict(ids),'note':'Descriptive diagnostic comparison, not a causal model ablation. Text reported separately.'}

def stats(values):
 vals=sorted(v for v in values if isinstance(v,(int,float))and not isinstance(v,bool)and math.isfinite(v)and v>=0)
 return {'n':len(vals),'median':statistics.median(vals)if vals else None,'p95':vals[max(0,math.ceil(.95*len(vals))-1)]if vals else None,'zero_n':sum(v==0 for v in vals)}

def telemetry(predictions):
 timings=collections.defaultdict(list);cache=collections.Counter();invoked=collections.Counter();attempts=[];reservations=[];devices=collections.Counter();tokens=[];token_costs=[]
 for p in predictions:
  timing=p.get('timing')or{};paired_timing=p.get('paired_timing')or{};hit=p.get('cache_hit',timing.get('cache_hit'));cache['hit'if hit is True else'miss'if hit is False else'unknown']+=1
  for section,data in [('timing',timing),('paired_timing',paired_timing)]:
   for key,value in data.items():
    if key.endswith('_seconds'):timings[section+'.'+key].append(value)
  for key in ['latency_seconds','elapsed_seconds','application_seconds','end_to_end_seconds']:
   if key in p:timings[key].append(p[key])
  hybrid=p.get('hybrid')or{};meta=p.get('provider')or{};v=p.get('provider_invoked',hybrid.get('provider_invoked',meta.get('invoked')));invoked['yes'if v is True else'no'if v is False else'unknown']+=1
  for container in [p,hybrid,meta]:
   val=container.get('actual_attempts',container.get('http_attempts',container.get('provider_attempts')))
   if isinstance(val,int):attempts.append(val);break
  for container in [p,hybrid,meta]:
   val=container.get('estimated_usd_reserved',container.get('reserved_usd'))
   if isinstance(val,(int,float)):reservations.append(val);break
  for key in ['device','actual_device','execution_device']:
   if p.get(key):devices[str(p[key])]+=1;break
  generations=p.get('generation',[])
  if not isinstance(generations,list):generations=[]
  if p.get('usage'):generations=generations+[{'usage':p['usage'],'model':p.get('model')}]
  for gen in generations:
   usage=gen.get('usage')or{};tokens.append(usage)
   from v2.gemini import MODEL_PRICES
   price=MODEL_PRICES.get(gen.get('model'));inp=usage.get('input_tokens');out=usage.get('output_tokens');thinking=usage.get('thinking_tokens',0)
   if price and isinstance(inp,int)and isinstance(out,int)and isinstance(thinking,int):token_costs.append((inp*price[0]+(out+thinking)*price[1])/1e6)
 return {'records':len(predictions),'cache_status':dict(cache),'provider_invocation':dict(invoked),'http_attempts_known_sum':sum(attempts),'http_attempts_recorded_n':len(attempts),'reservation_usd_known_sum':sum(reservations),'reservation_recorded_n':len(reservations),'cost_note':'Reservations are ceilings, not actual billed cost. Missing usage/cost remains unknown; never imputed zero. Ledger/dashboard reconcile separately.','usage_recorded_n':len(tokens),'usage_known_tokens':{k:sum(u[k]for u in tokens if isinstance(u.get(k),int))for k in ['input_tokens','output_tokens','thinking_tokens']},'token_price_estimate_usd_known_sum':sum(token_costs),'token_price_estimate_generation_n':len(token_costs),'token_price_note':'Estimate from recorded tokens and existing MODEL_PRICES, not dashboard billing. Missing thinking usage is not imputed when explicitly null.','execution_device':dict(devices),'timing':{k:stats(v)for k,v in timings.items()},'timing_note':'Only recorded phases summarized. Cache unknown is not cold inference; shared preprocessing is not charged once per question by this scorer.'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,default=RESULTS_ROOT/'agile1/experiment');parser.add_argument('--inference-complete',action='store_true',help='Explicitly authorize offline reference access only after inference is finished');args=parser.parse_args()
 if not args.inference_complete:raise SystemExit('Refusing early scoring: supply --inference-complete after all inference has finished.')
 folder=args.folder;selection=json.loads((folder/'selection.json').read_text());questions=read_rows(folder/'questions.jsonl')
 if sha(folder/'questions.jsonl')!=selection['questions_sha256']:raise ValueError('Frozen questions hash mismatch')
 gold={r['sample_id']:r for r in read_rows(ROOT/'benchmarks/qa-v3/quick.answers.jsonl')};qids={q['sample_id']for q in questions};cases={r['sample_id']:r for r in selection['cases']};predictions={};provenance={}
 for mode in MODES:
  path=folder/(mode+'.predictions.jsonl');items=read_rows(path)if path.exists()else[];ids=[r['sample_id']for r in items]
  if len(ids)!=len(set(ids))or set(ids)-qids:raise ValueError(mode+': duplicate or unmatched prediction IDs')
  predictions[mode]={r['sample_id']:r for r in items};provenance[mode]={'path':str(path),'sha256':sha(path)if path.exists()else None,'recorded_n':len(items)}
 rows=[]
 for q in questions:
  sid=q['sample_id'];g=gold[sid]
  if(g['path'],g['question'])!=(q['path'],q['question']):raise ValueError('Gold/input identity mismatch: '+sid)
  row={'sample_id':sid,'drawing_id':cases[sid]['group'],'path':q['path'],'format':Path(q['path']).suffix.lower(),'type':g['type'],'target':g.get('category','unknown'),'source':g.get('source','unknown')}
  for mode in MODES:
   p=predictions[mode].get(sid)
   if p and any(p.get(k,q[k])!=q[k]for k in ['path','question']):raise ValueError(mode+': input mismatch '+sid)
   row[mode]=classify(g,p)
  rows.append(row)
 result={'diagnostic_development_only':True,'selection':{'n':len(rows),'seed':selection['seed'],'questions_sha256':sha(folder/'questions.jsonl'),'unique_drawing_groups':len({r['drawing_id']for r in rows}),'physical_source_files':len({r['path']for r in rows})},'limitations':['32 deterministic diagnostic development questions, not representative accuracy or a held-out benchmark.','Custom model trained on CubiCasa; overlap is possible and not certified absent.','Original v3 numeric scoring unchanged; text uses existing conservative text-rubric-1 and remains ungraded where unsupported.','No mixed full-run/small-run denominators. Missing predictions remain in all-mode manifest denominators.'],'modes':{m:summary(rows,m)for m in MODES},'paired':{a+'_vs_'+b:paired(rows,a,b)for a,b in [('local','hybrid'),('custom','hybrid'),('local','custom')]},'groups':{key:{v:{m:summary([r for r in rows if r[key]==v],m)for m in MODES}for v in sorted({r[key]for r in rows})}for key in ['format','type','target','source']},'telemetry':{m:telemetry(list(predictions[m].values()))for m in MODES},'provenance':{'predictions':provenance,'selection_sha256':sha(folder/'selection.json'),'quick_answers_sha256':sha(ROOT/'benchmarks/qa-v3/quick.answers.jsonl'),'numeric_scorer_sha256':sha(ROOT/'evaluation/numeric.py'),'text_scorer_sha256':sha(ROOT/'evaluation/text.py'),'scorer_sha256':sha(Path(__file__))}}
 write_json(folder/'score.json',result);(folder/'scored-rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows));print(json.dumps({'modes':result['modes'],'paired':result['paired']},indent=2))
if __name__=='__main__':main()
