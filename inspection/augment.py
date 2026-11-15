from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Add matched, version-labelled saved-run comparisons and precise legacy curation audit."""
import json,sqlite3,collections
from qa.common import ROOT,write_json
from .analytics import summarize,make_row,write_report
O=RESULTS_ROOT/'inspection'
def augment():
 s=json.loads((O/'summary.json').read_text());c=sqlite3.connect(O/'index.sqlite3');comparisons={}
 for label,a,b in [('v3 frozen40','v3-paired-local','v3-paired-hybrid'),('v2 final frozen40','v2-final-paired-a1','v2-final-paired-a2'),('audit4 fixed60 raw','audit4-local','audit4-hybrid'),('audit4 fixed60 unit-only replay','audit4-local','audit4-hybrid-unit-fixed')]:
  ar={id:json.loads(row)for id,row in c.execute('SELECT id,row FROM predictions WHERE run=?',(a,))};br={id:json.loads(row)for id,row in c.execute('SELECT id,row FROM predictions WHERE run=?',(b,))};ids=sorted(set(ar)&set(br));paired=[i for i in ids if ar[i]['path']==br[i]['path']and ar[i]['question']==br[i]['question']];states=collections.Counter()
  for i in paired:
   x,y=ar[i],br[i]
   if x['question_type']not in ['count','area','volume','length']:states['ungraded_text']+=1;continue
   left=x['outcome']=='Correct';right=y['outcome']=='Correct';states['unchanged_correct'if left and right else'rescue'if right else'regression'if left else'unresolved_or_wrong']+=1
  comparisons[label]={'local_run':a,'hybrid_run':b,'matched_ids':len(paired),'question_or_path_mismatch':len(ids)-len(paired),'states':dict(states),'local':summarize([ar[i]for i in paired]),'hybrid':summarize([br[i]for i in paired]),'note':'Matched existing questions, version/configuration sources recorded separately. Not a causal ablation; audit4 unit-only result is explicitly post-hoc.'}
 legacy=json.loads((RESULTS_ROOT/'v2/replay-delivery/index.json').read_text());allrecords=legacy['records'];curated=[r for r in allrecords if any(m['correct']for m in r['modes'].values())][:20];exported={(r['sample_id'],mode)for r in allrecords for mode in r['modes']};visible={(r['sample_id'],mode)for r in curated for mode,m in r['modes'].items()if m['correct']};s['legacy_replay']['default_curated_questions']=len(curated);s['legacy_replay']['default_visible_mode_records']=len(visible);s['legacy_replay']['exported_mode_records_hidden_by_default']=len(exported-visible);s['legacy_replay']['absent_hybrid_exports']=[r['sample_id']for r in allrecords if 'hybrid'not in r['modes']];s['comparisons']=comparisons
 per_run={}
 for run in s['runs']:
  entries={id:json.loads(row)for id,row in c.execute('SELECT id,row FROM predictions WHERE run=?',(run['id'],))};gs=[json.loads(g)for(g,)in c.execute('SELECT gold FROM questions WHERE manifest=?',(run['manifest'],))];rows=[entries.get(g['sample_id'])or make_row(run['id'],run['mode'],g,None)for g in gs];per_run[run['id']]=summarize(rows)
 s['primary_local']['unique_input_files']=len({json.loads(r[0])['path']for r in c.execute('SELECT row FROM predictions WHERE run=?',('v3-release-quick',))});s['primary_hybrid_absent']['unique_input_files']=s['primary_local']['unique_input_files'];s['per_run_summaries']=per_run;write_json(O/'summary.json',s);write_report(s)
 with(RESULTS_ROOT/'inspection/HISTORICAL_ANALYTICS.md').open('a')as f:
  f.write('\n## Local versus Hybrid on matched saved questions\n\n|Comparison|Matched|Local numeric|Hybrid numeric|Rescues|Regressions|Unchanged correct|Unresolved/wrong|\n|---|---:|---:|---:|---:|---:|---:|---:|\n')
  for label,v in comparisons.items():
   a,b=v['local'],v['hybrid'];st=v['states'];f.write(f"|{label}|{v['matched_ids']}|{a['correct']}/{a['scorable_n']}|{b['correct']}/{b['scorable_n']}|{st.get('rescue',0)}|{st.get('regression',0)}|{st.get('unchanged_correct',0)}|{st.get('unresolved_or_wrong',0)}|\n")
  f.write(f"\nOld default replay exposed{len(visible)} mode records across20 curated questions; **{len(exported-visible)} exported mode records were hidden by curation**, not absent from disk. Only{len(s['legacy_replay']['absent_hybrid_exports'])} legacy question IDs genuinely lack a Hybrid export: {', '.join(s['legacy_replay']['absent_hybrid_exports'])}. Those supplemental A0 records must not be mistaken for absent v3 predictions or silently filled with another version. Full per-run/mode LEFT JOIN summaries and provenance are in summary.json.\n")
 c.close();print('Matched comparisons and exact curation reconciliation saved')
if __name__=='__main__':augment()
