"""Answer-free final eligibility quarantine. Never opens holdout/full reference answers."""
import sys,json,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,sha,write_json
from runtime_paths import RESULTS_ROOT
O=RESULTS_ROOT/'iteration60/final-evaluation';O.mkdir(parents=True,exist_ok=True)
if(O/'questions.jsonl').exists():raise SystemExit('Final candidate already frozen; preserve it')
inv=json.loads((ROOT/'benchmarks/qa-v3/file-inventory.json').read_text());occupied=set();provenance=[]
# Exclude entire previously exposed/custom-training source partitions conservatively.
paths=[ROOT/'benchmarks/qa-v3'/n for n in['quick.questions.jsonl','smoke.questions.jsonl','train_candidates.questions.jsonl','exposed_holdout.questions.jsonl']]+[RESULTS_ROOT/'v3/reserved50/questions.jsonl',RESULTS_ROOT/'audit4/diagnostic.questions.jsonl']
for path in paths:
 if not path.exists():continue
 occupied.update(q['path']for q in(json.loads(l)for l in path.open()));provenance.append({'path':str(path.relative_to(ROOT))if path.is_relative_to(ROOT)else path.name,'sha256':sha(path)})
# Every saved prediction source was inspected/development/exposed; exclude at drawing identity.
for path in(RESULTS_ROOT).rglob('*predictions.jsonl'):
 if 'iteration60'in path.parts:continue
 for line in path.open():
  try:q=json.loads(line)
  except ValueError:continue
  if q.get('path')in inv:occupied.add(q['path'])
# Known spatial annotations/custom training identities, including quarantines, stay excluded.
for path in(RESULTS_ROOT/'audit4').glob('spatial*.json'):
 data=path.read_text()
 for name in inv:
  if name in data:occupied.add(name)
 groups={inv[p].get('group')for p in occupied if p in inv};bytes_={inv[p].get('sha256')for p in occupied if p in inv};pixels={inv[p].get('pixel_sha256')for p in occupied if p in inv};groups.discard(None);bytes_.discard(None);pixels.discard(None)
exclusions_path=ROOT/'config/exploratory-exclusions.json'
if exclusions_path.exists():
 exclusions=json.loads(exclusions_path.read_text())['groups'];bytes_.update(e['source_sha256']for e in exclusions);pixels.update(e['pixel_sha256']for e in exclusions);groups.update(e['group']for e in exclusions)
questions=[json.loads(l)for l in(ROOT/'benchmarks/qa-v3/holdout.questions.jsonl').open()];eligible=[q for q in questions if q['path']in inv and inv[q['path']].get('group')not in groups and inv[q['path']].get('sha256')not in bytes_ and(not inv[q['path']].get('pixel_sha256')or inv[q['path']]['pixel_sha256']not in pixels)];eligible.sort(key=lambda q:(inv[q['path']].get('group',''),q['sample_id']));(O/'questions.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n'for q in eligible));write_json(O/'manifest.json',{'version':'final-eligibility-v1','questions_sha256':sha(O/'questions.jsonl'),'questions':len(eligible),'drawings':len({inv[q['path']].get('group')for q in eligible}),'excluded_known_paths':len(occupied),'exclusion_manifests':provenance,'inventory_sha256':sha(ROOT/'benchmarks/qa-v3/file-inventory.json'),'answers_read':False,'status':'provisional quarantine; manual provenance review required before final evaluation','limits':['Conservative exclusion of all train candidates, quick/smoke/exposed/reserved/diagnostic and saved-run drawing groups','Existing corrected group IDs and exact byte/pixel aliases used; no new similarity model','Preview alias identities share the full source groups; unknown near-duplicate/project aliases may remain','Pretrained overlap unknown; no final answers inspected or inference run']});print('Final provisional eligible',len(eligible),'questions')
