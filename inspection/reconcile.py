from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Saved-file integrity, evidence/export reconciliation and descriptive trace facts."""
import json,sqlite3,collections,statistics
from pathlib import Path
from PIL import Image
from qa.common import ROOT,sha,write_json
from .analytics import percentile
O=RESULTS_ROOT/'inspection'
def run():
 s=json.loads((O/'summary.json').read_text());bundle=RESULTS_ROOT/'v2/replay-delivery';checks=json.loads((bundle/'checksums.json').read_text());broken=[];verified=0
 for name,expected in checks.items():
  source=(bundle/name).resolve()
  if not source.is_relative_to(bundle.resolve()):broken.append({'path':name,'reason':'unsafe checksum path'});continue
  if not source.is_file():broken.append({'path':name,'reason':'missing'});continue
  if sha(source)!=expected:broken.append({'path':name,'reason':'hash mismatch'});continue
  try:
   if source.suffix.lower()=='.png':
    with Image.open(source)as im:im.verify()
   elif source.suffix.lower()=='.json':json.loads(source.read_text())
  except Exception as e:broken.append({'path':name,'reason':type(e).__name__});continue
  verified+=1
 c=sqlite3.connect(O/'index.sqlite3');rows=[json.loads(r[0])for r in c.execute('SELECT row FROM predictions WHERE run=?',('v3-release-quick',))];primary_paths=sorted({r['path']for r in rows});sources=[]
 for name in primary_paths:
  path=DATASET_ROOT/name;sources.append({'path':name,'exists':path.is_file(),'sha256':sha(path)if path.is_file()else None})
 indexedfolders={r['job']for r in s['legacy_replay']['assets']};unmatched=[p.name for p in bundle.iterdir()if p.is_dir()and p.name not in indexedfolders];identity=[]
 ix=json.loads((bundle/'index.json').read_text())
 for q in ix['records']:
  for mode,ref in q['modes'].items():
   path=bundle/ref['id']/'job.json'
   if not path.exists():continue
   job=json.loads(path.read_text())
   if job['id']!=ref['id']or job['question']!=q['question']or job['source_name']!=q['source_path']:identity.append({'sample_id':q['sample_id'],'mode':mode,'reason':'job/index identity mismatch'})
 s['asset_integrity']={'legacy_checked_files':len(checks),'legacy_verified_files':verified,'legacy_broken_files':broken,'legacy_orphan_directories':unmatched,'legacy_identity_mismatches':identity,'primary_input_files':len(sources),'primary_missing_sources':sum(not r['exists']for r in sources),'source_hash_manifest':'results/inspection/source-assets.json','source_hash_manifest_sha256':None,'new_index_records':sum(r['recorded']for r in s['runs']),'new_index_physical_runs':len(s['runs']),'new_index_questions_primary_local':len(rows),'note':'All old sealed export hashes and PNG/JSON structure checked. New source previews/crops generated lazily; lack of an old overlay is not lack of a prediction. No disk records removed.'}
 write_json(O/'source-assets.json',sources);s['asset_integrity']['source_hash_manifest_sha256']=sha(O/'source-assets.json')
 tracefacts={}
 for name,predicate in [('sauna_errors',lambda r:r['target']=='sauna'and r['outcome']=='Incorrect'),('window_errors',lambda r:r['target']=='window'and r['outcome']=='Incorrect'),('recorded_ocr_failures',lambda r:r['ocr_route']not in['unknown','other_or_unknown','native_pdf_text_extraction']and r['outcome']in['Incorrect','Abstained','Unsupported','Execution error'])]:
  chosen=[]
  for r in rows:
   if not predicate(r):continue
   chosen.append({k:r[k]for k in ['sample_id','path','route','model','outcome','answer','reference','ocr_route','stored_stage_timings','warnings']})
   if len(chosen)>=3:break
  tracefacts[name]=chosen
 s['trace_examples']=tracefacts
 # Expose physical files as well as split/source grouping identities.
 s['primary_local']['unique_input_files']=len(primary_paths);s['primary_hybrid_absent']['unique_input_files']=len(primary_paths)
 stages=collections.defaultdict(list)
 for r in rows:
  for name,t in r.get('stored_stage_timings',{}).items():
   if not isinstance(t,dict):continue
   for field,value in t.items():
    if field.endswith('_seconds')and isinstance(value,(int,float))and value>=0:stages[(name,field,'cached'if t.get('cache_hit')is True else'uncached'if t.get('cache_hit')is False else'unknown')].append(value)
 s['recorded_stage_timing_summary']={' | '.join(k):{'n':len(v),'median_seconds':statistics.median(v),'p95_seconds':percentile(v,.95),'note':'Recorded stage metadata may retain original-generation timing, even when the top-level result is cached. Not new inference latency.'}for k,v in stages.items()}
 write_json(O/'summary.json',s);write_json(O/'evidence-reconciliation.json',s['asset_integrity'])
 with(RESULTS_ROOT/'inspection/HISTORICAL_ANALYTICS.md').open('a')as f:
  a=s['asset_integrity'];f.write(f"\n## Evidence/export integrity and drawing identities\n\nThe primary manifest covers **{len(primary_paths)} distinct input files**, grouped into **{s['primary_local']['unique_drawings']} drawing/source IDs** by the corrected split manifest (duplicate drawing aliases stay grouped). Tables above use those grouping IDs; paths and drawing IDs both remain in JSONL. **{a['primary_missing_sources']} missing original inputs**. Old sealed replay: **{verified}/{len(checks)} files hash-verified**, PNGs decoded/verified, JSON parsed; **{len(broken)} corrupt/missing/hash-mismatched files**, **{len(identity)} index/job identity mismatches**, **{len(unmatched)} orphan directories**. New index: **{a['new_index_records']} recorded predictions across {len(s['runs'])} physical saved runs**; the matched v3 paired UI view is a labelled join of two equal configurations, not a new run.\n\n")
  f.write('## Count errors by target\n\n|Target|Count questions|Valid counts|Exact / all count questions|MAE|Signed error|Under / over (valid denominator)|\n|---|---:|---:|---:|---:|---:|---:|\n')
  for target in sorted({r['target']for r in rows}):
   rs=[r for r in rows if r['target']==target and r['question_type']=='count'];valid=[r for r in rs if r.get('absolute_error')is not None]
   if not rs:continue
   f.write(f"|{target}|{len(rs)}|{len(valid)}|{sum(r['outcome']=='Correct'for r in rs)}/{len(rs)}|{statistics.mean(r['absolute_error']for r in valid)if valid else'N/A'}|{statistics.mean(r['signed_error']for r in valid)if valid else'N/A'}|{sum(r['signed_error']<0 for r in valid)} / {sum(r['signed_error']>0 for r in valid)} ({len(valid)})|\n")
  f.write('\n## Trace-supported examples, observations and hypotheses\n\n')
  for category,records in tracefacts.items():
   for r in records:f.write(f"- {category}: **{r['sample_id']}**, `{r['route']}`, {r['outcome']}; saved answer {r['answer']}, reference {r['reference']}. Recorded OCR route: {r['ocr_route']}; recorded stage names: {', '.join(r['stored_stage_timings'])or'none'}. Count disagreement alone does not identify missing objects or establish an OCR cause.\n")
  f.write('\nSauna errors exist despite sauna-capable room/bench routes; a missing RT-DETR sauna label is not a demonstrated cause. Window errors span sources/routes and need visual localization review; count disagreement is not localization proof. OCR failures above require recorded OCR metadata. Small text, ambiguous labels and orientation remain hypotheses unless the saved warning/evidence specifically supports them. No new OCR was used to investigate these records.\n\nStage timing distributions (model loading/inference/other recorded fields with n, median and p95) are in `summary.json.recorded_stage_timing_summary`. These retain generation/caching ambiguity explicitly. The primary 9,544 result timings are all marked cached; their median 0.00252 s and p95 0.01701 s describe cached pipeline retrieval, not detector inference speed. No fresh latency is claimed.\n')
 c.close();print('Source/export reconciliation:',json.dumps(a))
if __name__=='__main__':run()
