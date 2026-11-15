"""Freeze diagnostic IDs from already-inspected development outcomes; inference sees no gold."""
import sys,json,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT
O=RESULTS_ROOT/'iteration60';O.mkdir(parents=True,exist_ok=True)
if(O/'questions.jsonl').exists():raise SystemExit('Preserve existing selection')
gold={q['sample_id']:q for q in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};pred={q['sample_id']:q for q in(json.loads(l)for l in(RESULTS_ROOT/'v3/release-quick/predictions.jsonl').open())};used=set();chosen=[]
criteria=[('PNG fixtures',4,lambda g,p:g['source']=='cubicasa5k'and g['category']in['count_sinks','count_toilet_fixtures','count_showers_and_baths']),('PNG windows',2,lambda g,p:g['source']=='cubicasa5k'and g['category']=='count_windows'),('Swiss PDF doors',4,lambda g,p:g['source']=='swiss_dwellings'and g['category']=='count_doors'),('PDF area abstentions',3,lambda g,p:g['path'].endswith('.pdf')and g['type']=='area'and p['status']=='abstained'),('IFC properties',3,lambda g,p:g['path'].endswith('.ifc')and g['type']=='text')]
for label,n,condition in criteria:
 candidates=[g for id,g in gold.items()if id in pred and condition(g,pred[id])and g.get('language')=='en'];candidates.sort(key=lambda g:hashlib.sha256(('paired60-v1:'+g['sample_id']).encode()).hexdigest());added=0
 for g in candidates:
  group=g.get('group_id',g['path'])
  if group in used:continue
  used.add(group);chosen.append((label,g));added+=1
  if added==n:break
 # IFC has only a few distinct drawings; permit different semantics on one drawing.
 if added<n:
  for g in candidates:
   if g['sample_id']in{q['sample_id']for _,q in chosen}:continue
   chosen.append((label,g));added+=1
   if added==n:break
questions=[{k:g[k]for k in ['sample_id','path','question']}for _,g in chosen];(O/'questions.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n'for q in questions));write_json(O/'selection.json',{'version':'paired60-v1','questions_sha256':sha(O/'questions.jsonl'),'n':len(questions),'drawings':len({g.get('group_id',g['path'])for _,g in chosen}),'cases':[{'id':g['sample_id'],'group':g.get('group_id'),'stratum':label,'category':g['category'],'saved_local_status':pred[g['sample_id']]['status']}for label,g in chosen],'note':'Diagnostic DEVELOPMENT, not representative; deterministic hash order, no duplicate translations; known strong and weak strata; inference file excludes all answers/grading labels.'});print('Frozen',len(questions),'questions')
# Brief already-saved failure inspection, no model invocation.
write_json(O/'preflight-failure-inspection.json',[{'id':g['sample_id'],'status':pred[g['sample_id']]['status'],'route':pred[g['sample_id']]['route'],'warnings':pred[g['sample_id']].get('warnings',[]),'observed_limit':'Saved trace only; no causal box-miss assumption'}for _,g in chosen if pred[g['sample_id']]['status']!='success'][:5])
