"""Answer-free provenance audit; original corrected split files are never changed."""
import json,hashlib,collections
from pathlib import Path
from .clock import atomic,now
from qa.common import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 dest=OUT/'final-eligibility'
 if(dest/'manifest.json').exists():raise ValueError('Audit is frozen; preserve it')
 inv=json.loads((ROOT/'benchmarks/qa-v3/file-inventory.json').read_text());source=ROOT/'results/iteration60/final-evaluation/questions.jsonl';questions=[json.loads(l)for l in source.open()];occupied=set();provenance=[]
 manifests=[ROOT/'benchmarks/qa-v3'/n for n in ['quick.questions.jsonl','smoke.questions.jsonl','train_candidates.questions.jsonl','exposed_holdout.questions.jsonl']]
 manifests+=[ROOT/'results/v3/reserved50/questions.jsonl',ROOT/'results/audit4/diagnostic.questions.jsonl']
 manifests+=list((ROOT/'results/v3').glob('*training/manifest.json'))
 for path in manifests:
  if not path.is_file():continue
  rows=[json.loads(l)for l in path.open()]if path.suffix=='.jsonl'else json.loads(path.read_text()).get('files',[])
  occupied.update(r['path']for r in rows if r.get('path')in inv);provenance.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'source_records':len(rows)})
 # Previous inference outputs expose their source groups, regardless of their scores.
 for path in(ROOT/'results').rglob('*predictions.jsonl'):
  if 'final-evaluation'in path.parts or 'final-eligibility'in path.parts:continue
  for line in path.open():
   try:r=json.loads(line)
   except ValueError:continue
   if r.get('path')in inv:occupied.add(r['path'])
 groups={inv[p]['group']for p in occupied};bytes_={inv[p]['sha256']for p in occupied};pixels={inv[p]['pixel_sha256']for p in occupied if inv[p].get('pixel_sha256')};small_hashes={int(inv[p]['dhash64'],16)for p in occupied if inv[p].get('dhash64')};pdf_hashes={inv[p]['pdf_first_page_dhash']for p in occupied if inv[p].get('pdf_first_page_dhash')}
 rows=[];eligible=[];known=[];uncertain=[]
 for q in questions:
  item=inv[q['path']];reason=[]
  if item['group']in groups:reason.append('known_training_or_exposed_project')
  if item['sha256']in bytes_:reason.append('known_exact_file_alias')
  if item.get('pixel_sha256')in pixels:reason.append('known_exact_pixel_alias')
  if item.get('dhash64')and any((int(item['dhash64'],16)^h).bit_count()<=2 for h in small_hashes):reason.append('conservative_near_image_alias_hamming_le_2')
  if item.get('pdf_first_page_dhash')in pdf_hashes:reason.append('conservative_matching_pdf_overview_hash')
  overlap='unknown_custom_cubicasa4200_training_membership'if 'cubicasa5k'in q['path']else'no_known_local_training_or_dev_overlap; pretrained_overlap_unknown'
  row={'sample_id':q['sample_id'],'path':q['path'],'group':item['group'],'sha256':item['sha256'],'excluded_reasons':reason,'training_overlap_status':overlap};rows.append(row)
  if not reason:
   eligible.append(q);(uncertain if 'cubicasa5k'in q['path']else known).append(q)
 dest.mkdir(parents=True,exist_ok=True)
 for name,rs in [('questions.jsonl',eligible),('known-unexposed.questions.jsonl',known),('unknown-custom-overlap.questions.jsonl',uncertain),('audit.rows.jsonl',rows)]:
  (dest/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rs))
 atomic(dest/'manifest.json',{'time':now(),'source_manifest':str(source.relative_to(ROOT)),'source_sha256':sha(source),'original_questions':len(questions),'eligible_questions':len(eligible),'eligible_groups':len({inv[q['path']]['group']for q in eligible}),'known_unexposed_questions':len(known),'unknown_custom_training_overlap_questions':len(uncertain),'excluded_questions':len(questions)-len(eligible),'exclusion_reasons':dict(collections.Counter(reason for r in rows for reason in r['excluded_reasons'])),'provenance':provenance,'files':{p.name:sha(p)for p in dest.glob('*.jsonl')},'answers_read':False,'limits':['No final reference answers were opened.','Custom YOLO README reports4200 CubiCasa training plans but no identities; all CubiCasa final candidates remain unknown overlap, never certified unseen.','Canonical drawing/project groups, exact byte/pixel and conservative recorded overview hashes are checked; unknown aliases can remain.','Unknown external pretrained membership applies to every format.','Only evaluate after production freeze and completed deployment/submission delivery.']});print(json.dumps({k:v for k,v in json.loads((dest/'manifest.json').read_text()).items()if k not in ['provenance','files']},indent=2))
if __name__=='__main__':main()
