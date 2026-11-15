"""Reproducible compact reporting of immutable saved development comparisons."""
import json,collections
from pathlib import Path
from .clock import atomic,now
from qa.common import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 paths={'baseline':OUT/'baseline','local_specialists':OUT/'candidate-ensemble','best_offline':OUT/'candidate-pdf-recovery-v3','production_policy_estimate':OUT/'candidate-production-policy'};scores={k:json.loads((v/('summary.json'if k=='baseline'else'score.json')).read_text())for k,v in paths.items()};rows={k:{r['sample_id']:r for r in(json.loads(l)for l in(v/'rows.jsonl').open())}for k,v in paths.items()};matched={}
 for first in ['baseline','local_specialists']:
  counts=collections.Counter()
  for sid,r in rows['production_policy_estimate'].items():
   if not r['valid_reference']:continue
   before=rows[first][sid];a=before.get('correct',before.get('passed',False));b=r['correct'];counts['unchanged_correct'if a and b else'rescued'if b else'regressed'if a else'unresolved']+=1
  matched[first+'_to_production_policy']=dict(counts)
 dest=OUT/'development-report';dest.mkdir(exist_ok=True);atomic(dest/'summary.json',{'time':now(),'comparisons':matched,'files':{k:{'path':str(v.relative_to(ROOT)),'score_sha256':sha(v/('summary.json'if k=='baseline'else'score.json')),'rows_sha256':sha(v/'rows.jsonl')}for k,v in paths.items()},'scope':'All9544 quick questions are development. Proposal selectors are drawing-group out-of-fold estimates; saved observations reused. No untouched result and no fresh latency claim.'})
 lines=['# Overnight development comparison','',f'Generated {now()}. All 9,544 quick questions are DEVELOPMENT, across448 drawing/project groups. Fixed valid references9,471; narrative/ungraded73. Failures, abstentions and unsupported responses stay in the primary denominator. The primary target85% has not been reached.','', '|Candidate|Correct / valid references|Correct / all questions|Answer coverage|','|---|---:|---:|---:|']
 for k,r in scores.items():
  s=r if k=='baseline'else r['summary'];total=s.get('n',s.get('total'));correct=s['correct'];coverage=s.get('answer_coverage');lines.append(f"|{k}|{correct}/{s['valid_references']} ({100*s['primary_accuracy']:.2f}%)|{correct}/{total} ({100*s['correct_all']:.2f}%)|{100*coverage:.2f}%|"if coverage is not None else f"|{k}|{correct}/{s['valid_references']} ({100*s['primary_accuracy']:.2f}%)|{correct}/{total} ({100*s['correct_all']:.2f}%)|See frozen baseline rows|")
 lines+=['','The production-oriented policy keeps fast structural specialist routes rather than invoking review for the extra two correct opening questions. This is not a claim that a fresh live run reproduces every cached batched review: live single-question context can differ.','', '## Matched outcomes','', '|Comparison|Rescues|Regressions|Unchanged correct|Unresolved|','|---|---:|---:|---:|---:|']
 for k,c in matched.items():lines.append('|'+k+'|'+ '|'.join(str(c.get(s,0))for s in ['rescued','regressed','unchanged_correct','unresolved'])+'|')
 s=scores['production_policy_estimate']['summary'];n=s['numeric'];lines+=['',f"Count errors on {n['count_error_n']} valid answered count predictions: MAE {n['count_mae']:.6f}; signed bias {n['count_bias']:.6f}; undercounts {n['under_count']}, overcounts {n['over_count']}. This error denominator excludes unanswered counts; primary correctness does not. Text:73 ungraded,0 graded; no invented semantic credit.",'','## Selected policy groups','','|Group|Correct / valid references|Answered / total|','|---|---:|---:|']
 for k,g in scores['production_policy_estimate']['groups'].items():
  if k.startswith(('format:','type:','target:')):lines.append(f"|{k}|{g['correct']}/{g['valid_references']}|{g['answered']}/{g['total']}|")
 lines+=['','## Evidence and limits','','Original v3 predictions and all alternative experiment outputs are preserved. Reusable custom detector observations:361sources,360success/1size-boundunsupported. Grounded Flash review:358successful scene observations/361attempted sources; final failed sources retain Local. These scene calls are not one fresh call per translated question. No localization precision/recall is claimed without compatible spatial ground truth.','', 'Known high-volume residuals include windows, doors, shower/bath fixtures and native-PDF room scope/areas. An absent class is not established as the sole cause. Model-proposed review regions are not verified object annotations.','', 'Timing in this comparison is cached; fresh browser/server timings are recorded separately in external deployment verification. Original evaluation manifest and graders remain unchanged.','', 'Reproduce: `.venv/bin/python -m campaign.report_development`. Machine summary: `results/overnight-20261115/development-report/summary.json`; question rows remain in the hashed run directories.']
 (ROOT/'docs/OVERNIGHT_DEVELOPMENT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(matched,indent=2))
if __name__=='__main__':main()
