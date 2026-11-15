"""Offline development scoring. Inference inputs never import this module."""
import sys,json,collections,statistics,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT
from evaluation import numeric,text

def summarize(rows,key):
 out=collections.Counter(r[key]['outcome']for r in rows);numeric_rows=[r for r in rows if r['type']in['count','area','length','volume']];graded=[r for r in rows if r[key]['outcome']in['Correct','Incorrect']];return {'total':len(rows),'numeric_n':len(numeric_rows),'correct':out['Correct'],'incorrect':out['Incorrect'],'ungraded':out['Ungraded'],'unresolved':out['Abstained']+out['Unsupported']+out['Provider error']+out['Execution error'],'outcomes':dict(out),'numeric_correct_all':out['Correct']/len(numeric_rows)if numeric_rows else None,'correct_graded_answered':out['Correct']/len(graded)if graded else None,'answered':sum(r[key]['status']=='success'and r[key]['answer']is not None for r in rows),'text_newly_graded':sum(r[key].get('text',{}).get('graded',False)for r in rows)}
def classify(g,p):
 grade=numeric.score(g,p);status=p.get('status');answer=p.get('answer');extra=text.score(g['answer'],answer,text.rule_for(g['question'],g['answer']))if g['type']=='text'else{}
 outcome='Correct'if grade['passed']is True else'Incorrect'if status=='success'and grade['passed']is False else'Ungraded'if status=='success'else'Abstained'if status=='abstained'else'Unsupported'if status=='unsupported'else'Provider error'if status=='provider_error'else'Execution error'
 return {'status':status,'answer':answer,'unit':p.get('unit'),'outcome':outcome,'numeric_grade':grade,'text':extra}
def main():
 a=argparse.ArgumentParser();a.add_argument('--run',default='paired-v2');args=a.parse_args();folder=RESULTS_ROOT/'iteration60'/args.run
 if not(folder/'run.json').exists():raise RuntimeError('Only complete frozen runs can be scored')
 accounting=json.loads((folder/'accounting.json').read_text());fresh=accounting['questions'];gold={g['sample_id']:g for g in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};local={r['sample_id']:r for r in(json.loads(l)for l in(folder/'local.predictions.jsonl').open())};hybrid={r['sample_id']:r for r in(json.loads(l)for l in(folder/'hybrid.predictions.jsonl').open())};questions=[json.loads(l)for l in(folder/'questions.jsonl').open()];rows=[];states=collections.Counter()
 for q in questions:
  id=q['sample_id'];g=gold[id];assert g['path']==q['path']and g['question']==q['question'];x,y=local[id],hybrid[id];r={'sample_id':id,'drawing_id':g.get('group_id',g['path']),'path':q['path'],'format':Path(q['path']).suffix.lower(),'type':g['type'],'target':g['category'],'local':classify(g,x),'hybrid':classify(g,y),'provider_invoked':fresh[id]['provider_invoked'],'provider_attempts':fresh[id]['actual_attempts'],'local_timing':x.get('paired_timing'),'hybrid_timing':y.get('timing'),'cache_hit':x.get('timing',{}).get('cache_hit')};rows.append(r)
  if g['type']=='text':states['text_ungraded']+=1;continue
  a,b=r['local']['outcome']=='Correct',r['hybrid']['outcome']=='Correct';states['unchanged_correct'if a and b else'rescue'if b else'regression'if a else'unresolved_or_wrong']+=1
 groups={}
 for key in['format','type','target']:
  groups[key]={v:{'local':summarize([r for r in rows if r[key]==v],'local'),'hybrid':summarize([r for r in rows if r[key]==v],'hybrid')}for v in sorted({r[key]for r in rows})}
 run=json.loads((folder/'run.json').read_text());summary={'run':run,'diagnostic_development_only':True,'local':summarize(rows,'local'),'hybrid':summarize(rows,'hybrid'),'paired_states':dict(states),'drawings':len({r['drawing_id']for r in rows}),'groups':groups,'provenance':{'questions_sha256':sha(folder/'questions.jsonl'),'local_sha256':sha(folder/'local.predictions.jsonl'),'hybrid_sha256':sha(folder/'hybrid.predictions.jsonl'),'numeric_scorer_sha256':sha(ROOT/'evaluation/numeric.py'),'text_rubric_sha256':sha(ROOT/'config/text-rubric.json')},'provider_invoked_questions':sum(bool(r['provider_invoked'])for r in rows),'provider_error_questions':sum(r['hybrid']['outcome']=='Provider error'for r in rows),'http_attempts':sum(r['provider_attempts']or 0 for r in rows),'reservation_usd':accounting['reserved_usd'],'token_price_estimate_usd':accounting['token_price_estimate_usd'],'accounting_sha256':sha(folder/'accounting.json'),'timing':{}}
 for label,values in [('local_answer',[r['local_timing']['local_answer_seconds']for r in rows]),('additional_gemini',[r['hybrid_timing']['additional_gemini_seconds']for r in rows if r['hybrid_timing']]),('cloud_queue',[r['hybrid_timing']['queue_wait_seconds']for r in rows if r['hybrid_timing']])]:
  values=sorted(values);summary['timing'][label]={'n':len(values),'median':statistics.median(values)if values else None,'p95':values[min(len(values)-1,int(.95*len(values)))]if values else None}
 write_json(folder/'score.json',summary);(folder/'scored-rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows));print(json.dumps({k:summary[k]for k in['local','hybrid','paired_states','http_attempts','reservation_usd']},indent=2))
if __name__=='__main__':main()
