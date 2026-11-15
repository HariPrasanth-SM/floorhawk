"""Current promoted-policy baseline and separate matched candidate only; no inference."""
import json,csv,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT
O=RESULTS_ROOT/'iteration60';H=O/'history';H.mkdir(exist_ok=True)
def ratio(n,d):return f'{n}/{d}'if d else'N/A (0 scorable)'
def main():
 candidate=O/'paired-v2';assert(candidate/'score.json').is_file(),'Score completed candidate first';s=json.loads((candidate/'score.json').read_text());baseline=json.loads((RESULTS_ROOT/'inspection/summary.json').read_text());report=ROOT/'SOLUTION_ANALYTICS.md';old=H/'SOLUTION_ANALYTICS.previous.md'
 if report.exists()and not old.exists():shutil.copyfile(report,old)
 payload={'current_default':'v3 policies + runtime infrastructure; no new full-dev run','candidate_promoted':False,'candidate':'paired-evidence-v2 (explicit opt-in)','matched_candidate':s,'frozen_full_dev_baseline':{'run':baseline['primary_run'],'local':baseline['primary_local'],'groups':baseline['groups'],'note':'Earlier frozen v3 source full-run; not rescored after runtime configuration refactor, not paired with small Hybrid scores.'},'previous_report_sha256':sha(old)if old.exists()else None,'text_rule':'text-rubric-1; narrative semantics ungraded; numeric evaluator unchanged'};write_json(O/'current-summary.json',payload);shutil.copyfile(candidate/'scored-rows.jsonl',O/'current-rows.jsonl')
 rows=[json.loads(l)for l in(candidate/'scored-rows.jsonl').open()]
 with(O/'current-rows.csv').open('w')as f:
  fields=['sample_id','drawing_id','path','format','type','target','local_outcome','hybrid_outcome','local_answer','hybrid_answer','provider_attempts'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({**{k:r[k]for k in fields if k in r},'local_outcome':r['local']['outcome'],'hybrid_outcome':r['hybrid']['outcome'],'local_answer':r['local']['answer'],'hybrid_answer':r['hybrid']['answer']})
 b=baseline['primary_local'];l=s['local'];h=s['hybrid'];run=s['run'];t=f'''# FloorHAWK current release analytics

Default remains **v3 policies**; the paired candidate is **opt-in and not promoted**. Runtime/configuration/Git improvements have no new full-development score. The9,544-question quick set is DEVELOPMENT, never final-test performance. Final eligibility questions are frozen separately without reading final answers or running them.

## Matched paired candidate — paired-evidence-v2

**{l['total']} questions / {s['drawings']} distinct drawing groups**, identical IDs and unchanged Local evidence for both modes. Deterministic diagnostic sample: PNG fixtures/windows, Swiss-PDF doors, PDF-area abstentions, IFC properties. It overweights known difficult cases; it is not a representative accuracy estimate. Source/config/manifest SHA256 and exact per-question rows are in external `results/iteration60/paired-v2/score.json` and `scored-rows.jsonl`.

|Mode|Questions|Numeric denominator|Correct|Incorrect|Answered|Ungraded answered|Unresolved/errors|Numeric correct/all|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|Local|{l['total']}|{l['numeric_n']}|{l['correct']}|{l['incorrect']}|{l['answered']}|{l['ungraded']}|{l['unresolved']}|{l['correct']}/{l['numeric_n']}|
|Hybrid|{h['total']}|{h['numeric_n']}|{h['correct']}|{h['incorrect']}|{h['answered']}|{h['ungraded']}|{h['unresolved']}|{h['correct']}/{h['numeric_n']}|

Paired states: `{json.dumps(s['paired_states'],sort_keys=True)}`. Actual provider invocation: {s['provider_invoked_questions']} questions, {s['http_attempts']} HTTP attempts, {s['provider_error_questions']} final provider/schema errors. Enabled Hybrid is not equivalent to a request or successful answer. Unresolved outcomes and Local answers are preserved.

Separate versioned text rubric: {h['text_newly_graded']} newly graded Hybrid text answers. Narrative semantics remain explicitly ungraded; no combined numeric/text headline is invented. Whole-string scalar/controlled aliases and explicit-list set metrics reject misleading substrings and supersets. Numeric units/tolerance rules are unchanged.

'''
 for key in['format','type','target']:
  t+='## Matched '+key+' outcomes\n\n|Group|N|Local correct / numeric|Hybrid correct / numeric|Local answered|Hybrid answered|Hybrid unresolved|\n|---|---:|---:|---:|---:|---:|---:|\n'
  for name,v in s['groups'][key].items():a,b2=v['local'],v['hybrid'];t+=f"|{name}|{a['total']}|{ratio(a['correct'],a['numeric_n'])}|{ratio(b2['correct'],b2['numeric_n'])}|{a['answered']}|{b2['answered']}|{b2['unresolved']}|\n"
 t+=f'''\n## Timing, cost and resource limits

V2 reused the EXACT saved Local answers/bundle hashes from V1; local extraction was not rerun for the second contract check. Shared document extraction cost is recorded once per bundle; per-question Local answering may include cached specialist lookups. Original cache-generation timing is not new cold inference time. Median/p95 and sample counts: `{json.dumps(s['timing'],sort_keys=True)}`. Extra cloud generation/wait is measured separately; run elapsed {run['total_seconds']:.3f}s. V1 Local runtime remains separately recorded; V2 adds cloud-only wall time. Queue initially2, global atomic lifetime reservations retained, max2 attempts/question; six HTTP starts/minute.

This V2 run reserved **${s['reservation_usd']:.3f}**, {s['http_attempts']} attempts; this is conservative reservation, not settled billing. Actual token usage and current registered price calculation are in generation metadata and the accounting report. Lifetime limits remain1,000/$10, never reset. Original user-reported dashboard143 requests/$0.48 remains historical and unreconciled to later runs; do not mix it with this iteration. Resource samples and actual recorded device/cache flags remain external under iteration60. No final-test, paid training, public deployment or new model download occurred.

## Frozen full-development baseline — separate earlier run

Earlier frozen v3 Local: **{b['correct']}/{b['scorable_n']} (70.12%) numeric**, {b['total']} questions, {b['unique_drawings']} drawing groups/452 physical input paths. Correct6,641; Incorrect2,350; answered-ungraded20; abstained469; unsupported64; errors0; missing Local0. Coverage9,011/9,54494.42%; correct/graded answered6,641/8,99173.86%. Count MAE0.666586 on8,254 valid counts. Full-quick Hybrid does not exist. **Do not compare this full baseline against the small Hybrid sample as a paired result.** All full-run pipeline timings are cached retrieval; unknown original model times are not filled with zero. Full original row outputs/hashes remain external and unchanged.

'''
 for key in['format','question_type','target']:
  t+='### Full frozen baseline by '+key+'\n\n|Group|N|Recorded|Answered|Correct / scorable|Incorrect|Ungraded|Abstained/unsupported/errors|\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
  for name,v in baseline['groups'][key].items():t+=f"|{name}|{v['total']}|{v['recorded']}|{v['answered']}|{ratio(v['correct'],v['scorable_n'])}|{v['incorrect']}|{v['answered_ungraded']}|{v['abstained']}/{v['unsupported']}/{v['execution_error']}|\n"
 t+='\n## Whole iteration setup and smoke accounting\n\n45 actual provider attempts:26 strict V1,17 corrected V2,2 paired UI smokes. Total conservative reservations$0.540; token-price estimate$0.057782. Global247 requests/$8.949 reserved of the unchanged1,000/$10 caps. These totals are NOT the matched V2 sample cost/score denominator. Original reused-operation counters are corrected in derivative accounting.json using append-only ledger row ranges; raw predictions remain immutable. Later unique UUID/rate/cache/projection guards were smoke-tested without another evaluation campaign.\n'
 t+='\n## Previous versus current\n\nEarlier v3 policy/full-dev baseline is preserved. V1 paired strict schema exposed an optional-region contract issue; V2 accepts only source-bounded proposals labelled unverified, while preserving all ID/unit/type checks. Same Local evidence was reused; fresh Hybrid generation was measured separately. This is not a causal model ablation or evidence of full-dataset improvement. History summaries live in reports/history; full old predictions/reports stay external with hashes. No model/threshold promotion follows this diagnostic.\n\nRegenerate current-only report: `.venv/bin/python scripts/current_analytics.py`. Rebuild complete replay index separately with `python -m inspection.analytics`; its all-version historical report is external, not this main current report.\n';report.write_text(t);(ROOT/'docs/current-analytics.md').write_text(t);print('Current-only analytics written')
if __name__=='__main__':main()
