"""Offline paired review analysis: measures proposals, never supplies gold to review."""
import json,collections,hashlib
from pathlib import Path
from evaluation.numeric import score
from .clock import atomic,now
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def apply_review(local,observation):
 target=local.get('task',{}).get('target')
 if target not in observation.get('requested',[])or local.get('task',{}).get('operation')!='count'or local.get('task',{}).get('filters'):return None
 if target in observation.get('uncertain',[]):return dict(local,status='abstained',answer=None,evidence=[],route='gemini.grounded-scene-review')
 entities=[e for e in observation['entities']if e['class']==target]
 return dict(local,status='success',answer=len(entities),unit='count',evidence=entities,route='gemini.grounded-scene-review',model={'name':observation['model']},gemini_review={'source_sha256':observation['source_sha256'],'prompt_sha256':observation['prompt_sha256'],'generation_seconds':observation['generation_seconds'],'proposed_localization':True},warnings=list(local.get('warnings',[]))+['Visual review localization is model-proposed, not spatial ground truth or proof of completeness.'])
def main():
 gold={r['sample_id']:r for r in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.answers.jsonl').open())};ps=[json.loads(l)for l in(OUT/'candidate-local/predictions.jsonl').open()];sources=json.loads((OUT/'review-selection.json').read_text())['sources'];hashes={r['source_sha256']for r in sources};result={}
 for folder in(OUT/'reviews').iterdir():
  obs={}
  for p in folder.glob('*.json'):
   if p.stem in hashes:
    r=json.loads(p.read_text())
    if r.get('status')=='success':obs[r['source_sha256']]=r
  records=[];groups=collections.defaultdict(list)
  for local in ps:
   h=local.get('source_sha256')
   if h not in obs:continue
   new=apply_review(local,obs[h])
   if new is None:continue
   g=gold[local['sample_id']];before=score(g,local)['passed']is True;after=score(g,new)['passed']is True;row={'sample_id':local['sample_id'],'path':g['path'],'drawing_group':g['group_id'],'target':local['task']['target'],'local':local['answer'],'proposed':new['answer'],'reference':g['answer'],'local_correct':before,'review_correct':after,'state':'rescue'if after and not before else'regression'if before and not after else'unchanged_correct'if after else'unresolved','uncertain':new['status']=='abstained'};records.append(row);groups[row['target']].append(row)
  summary=lambda rs:{'n':len(rs),'local_correct':sum(r['local_correct']for r in rs),'review_correct':sum(r['review_correct']for r in rs),'rescues':sum(r['state']=='rescue'for r in rs),'regressions':sum(r['state']=='regression'for r in rs),'unresolved':sum(r['state']=='unresolved'for r in rs),'drawings':len({r['drawing_group']for r in rs})}
  result[folder.name]={'observed_drawings':len(obs),'summary':summary(records),'by_target':{k:summary(v)for k,v in groups.items()},'rows':records,'estimated_generation_seconds':[r['generation_seconds']for r in obs.values()]}
 atomic(OUT/'paired-review-pilot-score.json',{'time':now(),'models':result,'role':'Fixed selected paired development diagnostic, not full-dev or held-out accuracy'});print(json.dumps({k:{j:v for j,v in x.items()if j not in ['rows','estimated_generation_seconds']}for k,x in result.items()}))
if __name__=='__main__':main()
