"""Evaluator-side contract and baseline freeze. Never imported by inference adapters."""
import json,collections,hashlib,shutil,subprocess,time
from pathlib import Path
from .clock import atomic,now
from qa.common import sha
from evaluation.numeric import score,number
from evaluation.text import rule_for,score as text_score
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 OUT.mkdir(exist_ok=True);dest=OUT/'baseline';dest.mkdir(exist_ok=True)
 if (dest/'contract.json').exists():print('Already frozen');return
 qs=ROOT/'benchmarks/qa-v3/quick.questions.jsonl';gs=ROOT/'benchmarks/qa-v3/quick.answers.jsonl';ps=ROOT/'results/v3/release-quick/predictions.jsonl';gold=[json.loads(l)for l in gs.open()];questions=[json.loads(l)for l in qs.open()];pred={p['sample_id']:p for p in (json.loads(l)for l in ps.open())};assert len(gold)==len(questions)==len(pred)==9544
 refs={};text_rules={};groups=collections.defaultdict(list);records=[]
 for g in gold:
  sid=g['sample_id'];p=pred.get(sid);typ=g['type'];valid=number(g['answer'])is not None if typ!='text'else rule_for(g['question'],g['answer'])!='free_form';text_rules[sid]=rule_for(g['question'],g['answer'])if typ=='text'else None
  grade=score(g,p)
  if typ=='text'and valid:grade=text_score(g['answer'],p.get('answer')if p else None,text_rules[sid]);grade['passed']=bool(p and p.get('status')=='success'and grade.get('passed'))
  passed=grade.get('passed')is True;refs[sid]=valid
  r={'sample_id':sid,'path':g['path'],'group':g['group_id'],'format':Path(g['path']).suffix.lower(),'source':g['source'],'type':typ,'category':g['category'],'language':g['language'],'reference_valid':valid,'passed':passed,'status':p.get('status')if p else'not_recorded','route':p.get('route')if p else None,'positive_reference':number(g['answer'])>0 if number(g['answer'])is not None else None,'absolute_error':grade.get('absolute_error'),'signed_error':grade.get('signed_error')};records.append(r)
  for k in ['format','source','type','category','route','language','positive_reference']:groups[k+':'+str(r[k])].append(r)
 summary={'n':len(gold),'valid_references':sum(refs.values()),'correct':sum(r['passed']for r in records),'reference_coverage':sum(refs.values())/len(refs),'primary_accuracy':sum(r['passed']for r in records)/sum(refs.values()),'correct_all':sum(r['passed']for r in records)/len(refs),'groups':{k:{'n':len(rs),'valid_references':sum(r['reference_valid']for r in rs),'correct':sum(r['passed']for r in rs),'statuses':dict(collections.Counter(r['status']for r in rs))}for k,rs in groups.items()}}
 manifest={'time':now(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'questions':{'path':str(qs.relative_to(ROOT)),'sha256':sha(qs),'n':len(questions)},'references':{'path':str(gs.relative_to(ROOT)),'sha256':sha(gs),'n':len(gold)},'baseline_predictions':{'path':str(ps.relative_to(ROOT)),'sha256':sha(ps),'n':len(pred)},'grader_sources':{str(p.relative_to(ROOT)):sha(p)for p in [ROOT/'evaluation/numeric.py',ROOT/'evaluation/text.py']},'count_rule':'exact finite integral numeric equality; abstained/unsupported/errors/missing remain incorrect','quantity_rule':'Existing evaluator: normalize m²/m^2,m³/m^3,metres/meters; exact normalized unit match; fixed relative2% tolerance, exact0reference; no relative error versus0','text_rule':'text-rubric-1, explicit scalar IFC aliases or explicit unordered string-list set exactness; unsupported narrative remains ungradable; no substring credit','primary_denominator':'All9544 development questions with valid frozen numeric or defensible text references, including execution failures/abstentions; also correct/all9544 and reference coverage','text_rules':text_rules,'valid_references':refs,'development_only':True,'target':.85,'resources':{'disk_reserve_gib':15,'modal_evaluation_gpu_workers':1,'modal_evaluation_max_estimate_usd':8,'gemini_authority':'Existing non-overlapping80USD presenter envelope within100USD canonical total; no new independently spendable ledger'}}
 atomic(dest/'contract.json',manifest);atomic(dest/'summary.json',summary);(dest/'rows.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in records));atomic(OUT/'state.json',{'started':now(),'phase':'optimize','baseline_commit':manifest['source_commit'],'baseline_primary':summary['primary_accuracy'],'best_verified':None,'submission_repo':'https://github.com/HariPrasanth-SM/floorhawk','presenter_unchanged':True})
 for name in ['numeric.py','text.py']:shutil.copy2(ROOT/'evaluation'/name,dest/name)
 print(json.dumps({k:v for k,v in summary.items()if k!='groups'}));print('Text rules',collections.Counter(x for x in text_rules.values()if x));print('Counts/units',collections.Counter(g.get('unit')for g in gold));print('Text dev examples',[(g['category'],str(g['answer'])[:120])for g in gold if g['type']=='text'][:10])
if __name__=='__main__':main()
