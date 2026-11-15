from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Reproducible saved-result LEFT JOIN, byte-offset index, and offline analytics.
Only this offline builder reads evaluator references; no inference imports/calls.
"""
import json,sqlite3,collections,statistics,hashlib,time,argparse,csv,re,os
from pathlib import Path
from qa.common import ROOT,sha,write_json
from qa_score import provided,CATEGORY_TARGET,percentile
OUT=RESULTS_ROOT/'inspection';DB=OUT/'index.sqlite3';NUMERIC={'count','area','length','volume'}
OUTCOMES=['Correct','Incorrect','Answered but ungraded','Abstained','Unsupported','Execution error','Not recorded']
def load(p):return json.loads(Path(p).read_text())
def lines(p):
 with Path(p).open()as f:
  for line in f:
   if line.strip():yield json.loads(line)
def outcome(g,p):
 if p is None:return 'Not recorded',{'passed':False,'reason':'missing'}
 status=p.get('status','invalid');grade=provided.score(g,p)
 if status=='abstained':return 'Abstained',grade
 if status=='unsupported':return 'Unsupported',grade
 if status!='success':return 'Execution error',grade
 if p.get('answer')is None:return 'Execution error',dict(grade,reason='success_without_answer')
 if g['type']not in NUMERIC or grade['passed']is None:return 'Answered but ungraded',grade
 return ('Correct'if grade['passed']else'Incorrect'),grade

def ocr_info(p):
 if not p:return 'unknown','unknown'
 warnings=' '.join(map(str,p.get('warnings',[]))).lower();kind=p.get('input_kind');st=p.get('stage_timings',{});ev=p.get('evidence',[])
 if 'used english ocr'in warnings:return 'rendered_pdf_ocr_recorded','unknown'
 explicit=any('ocr'in k.lower()and v for k,v in st.items()) or any(isinstance(v,dict)and any('ocr'in k.lower()and v2 is not None for k,v2 in v.items())for v in st.values())
 methods=' '.join(str(e.get('method',''))for e in ev).lower()
 if explicit or 'tesseract'in methods or 'pp-ocr'in methods:return ('rendered_pdf_ocr_recorded'if kind=='pdf'else'raster_ocr_recorded'),'unknown'
 if kind=='pdf'and ('native text'in methods or str(p.get('route','')).startswith('pdf.native')):return 'native_pdf_text_extraction','unknown'
 return 'other_or_unknown','unknown'
def format_of(path):
 ext=Path(path).suffix.lower();return 'PNG'if ext=='.png'else'Other raster'if ext in['.jpg','.jpeg','.tif','.tiff','.bmp','.webp']else'PDF'if ext=='.pdf'else'SVG'if ext=='.svg'else'IFC'if ext=='.ifc'else'Other'
def model_label(p):
 m=p.get('model')or{}
 if isinstance(m,str):return m
 return str(m.get('name')or m.get('repository')or m.get('tool')or m.get('source')or'not recorded')
def summarize(rows):
 n=len(rows);counts=collections.Counter(r['outcome']for r in rows);numeric=[r for r in rows if r['question_type']in NUMERIC];graded=[r for r in rows if r['outcome']in['Correct','Incorrect']];answered=[r for r in rows if r['answer_present']];valid_counts=[r for r in rows if r['question_type']=='count'and r.get('absolute_error')is not None];timings={}
 for state in ['cached','uncached','unknown']:
  rs=[r for r in rows if r['cache_state']==state];values=[r['pipeline_seconds']for r in rs if r['pipeline_seconds']is not None];timings[state]={'rows':len(rs),'recorded_n':len(values),'missing_n':len(rs)-len(values),'zero_n':sum(v==0 for v in values),'median_seconds':statistics.median(values)if values else None,'p95_seconds':percentile(values,.95)}
 quantities={}
 for typ in ['count','area','length','volume']:
  valid=[r for r in rows if r['question_type']==typ and r.get('absolute_error')is not None];relative=[r['absolute_error']/abs(r['reference_numeric'])for r in valid if r.get('reference_numeric')not in(None,0)];quantities[typ]={'valid_n':len(valid),'mae':statistics.mean(r['absolute_error']for r in valid)if valid else None,'signed_bias':statistics.mean(r['signed_error']for r in valid)if valid else None,'under_n':sum(r['signed_error']<0 for r in valid),'over_n':sum(r['signed_error']>0 for r in valid),'exact_n':sum(r['signed_error']==0 for r in valid),'mean_relative_error_nonzero':statistics.mean(relative)if relative else None,'relative_nonzero_n':len(relative)}
 return {'total':n,'unique_drawings':len({r['drawing_id']for r in rows}),'unique_input_files':len({r['path']for r in rows}),'recorded':sum(r['recorded']for r in rows),'answered':len(answered),'correct':counts['Correct'],'incorrect':counts['Incorrect'],'answered_ungraded':counts['Answered but ungraded'],'abstained':counts['Abstained'],'unsupported':counts['Unsupported'],'execution_error':counts['Execution error'],'not_recorded':counts['Not recorded'],'answer_coverage':len(answered)/n if n else None,'scorable_n':len(numeric),'correct_all_scorable':counts['Correct']/len(numeric)if numeric else None,'graded_answered_n':len(graded),'correct_graded_answered':counts['Correct']/len(graded)if graded else None,'outcomes':{k:counts[k]for k in OUTCOMES},'quantities':quantities,'timings':timings}

def evidence_info(g,p):
 source=(DATASET_ROOT/g['path']).resolve();safe=source.is_relative_to((DATASET_ROOT).resolve());exists=safe and source.is_file()
 if p is None:return 'no_prediction','none',exists
 ev=p.get('evidence',[])
 if not ev:return 'no_localized_evidence_recorded','none',exists
 kinds=[]
 if any(e.get('guid')or e.get('property')for e in ev):kinds.append('IFC properties/GUIDs')
 if any(e.get('bbox')for e in ev):kinds.append('localized boxes')
 if any(e.get('polygon')for e in ev):kinds.append('polygons')
 return ('source_available'if exists else'source_missing'),'+'.join(kinds)or'nonspatial facts',exists

def make_row(run,mode,g,p):
 label,grade=outcome(g,p);p=p or{};recorded=bool(p);present=recorded and p.get('status')=='success'and p.get('answer')is not None;eav,etype,source=evidence_info(g,p if recorded else None);ocr,orientation=ocr_info(p);tm=p.get('timing')or{};state='cached'if tm.get('cache_hit')is True else'uncached'if tm.get('cache_hit')is False else'unknown';ref=provided.number(g['answer'])if g['type']in NUMERIC else None
 row={'run_id':run,'mode':mode,'sample_id':g['sample_id'],'drawing_id':g.get('group_id')or g['path'],'path':g['path'],'input_format':format_of(g['path']),'dataset':g.get('source')or str(Path(g['path']).parent),'question_type':g['type'],'target':CATEGORY_TARGET.get(g.get('category'))or p.get('task',{}).get('target')or g.get('category','unknown'),'recorded_target':p.get('task',{}).get('target'),'category':g.get('category','unknown'),'language':g.get('language','unknown'),'question':g['question'],'outcome':label,'recorded':recorded,'execution_status':p.get('status','not_recorded'),'answer_present':present,'answer':p.get('answer'),'unit':p.get('unit'),'grading_status':('correct'if grade['passed']is True else'incorrect'if label=='Incorrect'else'ungraded'if label=='Answered but ungraded'else'not_answered'),'grade_reason':grade['reason'],'reference':g['answer'],'reference_unit':g.get('unit'),'reference_numeric':ref,'route':p.get('route','not recorded'),'model':model_label(p),'combination':model_label(p)+' | '+','.join(sorted(p.get('stage_timings',{}))),'evidence_availability':eav,'evidence_type':etype,'source_available':source,'replay_availability':'indexed_record'if recorded else'no_prediction_for_run_mode','ocr_route':ocr,'ocr_orientation':orientation,'cache_state':state,'pipeline_seconds':tm.get('total_seconds'),'model_loading_seconds':tm.get('model_loading_seconds'),'inference_seconds':tm.get('inference_seconds'),'stored_stage_timings':p.get('stage_timings',{}),'warnings':p.get('warnings',[]),'normalized_reference_unit':provided.unit(g.get('unit'))}
 for key in ['absolute_error','signed_error']:row[key]=grade.get(key)
 return row

def prediction_files():
 files=sorted((RESULTS_ROOT).rglob('predictions.jsonl'))
 files +=[RESULTS_ROOT/'audit4'/n for n in ['local.predictions.jsonl','hybrid.predictions.jsonl','hybrid-unit-fixed.predictions.jsonl']if(RESULTS_ROOT/'audit4'/n).exists()]
 return files

def build():
 OUT.mkdir(exist_ok=True);temp=DB.with_suffix('.building.sqlite3')
 if temp.exists():raise RuntimeError('Previous temporary index exists; preserve or inspect before rebuilding')
 c=sqlite3.connect(temp);c.executescript('CREATE TABLE questions(manifest TEXT,id TEXT,gold TEXT,PRIMARY KEY(manifest,id));CREATE TABLE runs(id TEXT PRIMARY KEY,manifest TEXT,info TEXT);CREATE TABLE predictions(run TEXT,mode TEXT,id TEXT,offset INTEGER,length INTEGER,row TEXT,PRIMARY KEY(run,mode,id));CREATE INDEX pred_filter ON predictions(run,mode);')
 goldpaths=[ROOT/'benchmarks/qa-v3/quick.answers.jsonl',ROOT/'benchmarks/qa-v3/smoke.answers.jsonl',ROOT/'benchmarks/v2/paired.answers.jsonl',RESULTS_ROOT/'v3/reserved50/answers.offline-only.jsonl'];gold_by_id={};known={};goldsets={}
 for path in goldpaths:
  if not path.exists():continue
  gs=list(lines(path));question=path.with_name(path.name.replace('.answers','.questions'))
  if 'reserved50'in str(path):question=path.parent/'questions.jsonl'
  if question.exists():known[sha(question)]=str(path)
  goldsets[str(path)]=gs
  for g in gs:gold_by_id.setdefault(g['sample_id'],g)
 # Existing legacy5 references are evaluator records, not generated labels.
 legacy=load(RESULTS_ROOT/'v3/window-five/report.json')['samples'];legacy_gold={r['sample_id']:{'sample_id':r['sample_id'],'path':r['path'],'question':'How many windows are shown on this floor plan?','answer':r['expected'],'unit':'count','type':'count','category':'count_windows','source':'cubicasa5k','language':'en'}for r in legacy};gold_by_id.update(legacy_gold)
 files=prediction_files();catalog=[];excluded=[];manifest_written=set();primary=[];primary_hybrid=[];primary_id='v3-release-quick';legacy_index=load(RESULTS_ROOT/'v2/replay-delivery/index.json');legacy_records=legacy_index['records'];legacy_assets=[]
 for entry in legacy_records:
  for mode,ref in entry['modes'].items():
   dest=RESULTS_ROOT/'v2/replay-delivery'/ref['id'];jobfile=dest/'job.json';missing=[]
   if not jobfile.exists():missing=['job.json']
   else:
    job=load(jobfile)
    for pg in job.get('pages',[]):
     for n in [f"page-{pg['page']}.png",f"annotated-{pg['page']}.png"]:
      if not(dest/n).is_file():missing.append(n)
   legacy_assets.append({'id':entry['sample_id'],'mode':mode,'job':ref['id'],'missing_assets':missing})
 for number,path in enumerate(files):
  relative=str(path.relative_to(ROOT));run_id=relative.replace('results/','').replace('/predictions.jsonl','').replace('.predictions.jsonl','').replace('/','-');runmeta=load(path.parent/'run.json')if(path.parent/'run.json').exists()else{};settings=runmeta.get('settings',{});sample_records=[];errors=[];seen=set();mode=None;line_count=0
  # First lightweight scan discovers exact record IDs and verifies schema, without inference.
  with path.open('rb')as f:
   for lineno,raw in enumerate(f,1):
    line_count+=1
    try:p=json.loads(raw)
    except Exception:errors.append({'line':lineno,'reason':'corrupt JSON'});continue
    if 'sample_id'not in p or 'question'not in p:continue
    sample_records.append((p['sample_id'],p.get('path'),p['question'],p.get('execution_mode')))
  if not sample_records:excluded.append({'path':relative,'reason':'No question-level sample_id/question schema (e.g. spatial detector collection)','lines':line_count});continue
  manifest_path=known.get(settings.get('questions_sha256'));reportpath=path.parent/'report.json';report=load(reportpath)if reportpath.exists()else{}
  if not manifest_path and report.get('answers_sha256'):
   manifest_path=next((gp for gp in goldsets if sha(gp)==report['answers_sha256']),None)
  if manifest_path:gs=goldsets[manifest_path];manifest_id=sha(manifest_path)
  else:
   ids={i[0]for i in sample_records};gs=[gold_by_id[id]for id in sorted(ids)if id in gold_by_id];manifest_id=hashlib.sha256(('derived-saved-ID-set:'+','.join(g['sample_id']for g in gs)).encode()).hexdigest();manifest_path='derived saved-ID subset; exact answers from registered existing evaluation references'
  if not gs:excluded.append({'path':relative,'reason':'No matching registered evaluator references; not silently remapped','lines':line_count});continue
  if manifest_id not in manifest_written:
   c.executemany('INSERT INTO questions VALUES(?,?,?)',[(manifest_id,g['sample_id'],json.dumps(g,ensure_ascii=False))for g in gs]);manifest_written.add(manifest_id)
  modes={m for _,_,_,m in sample_records if m in ['local','hybrid']};mode=settings.get('mode')or('hybrid'if any(n in relative for n in ['targeted-','inventory-pilot','flash-pilot','pro-pilot','hybrid'])else next(iter(modes))if len(modes)==1 else'local')
  if 'audit4/hybrid'in relative:mode='hybrid'
  if relative=='results/v3/release-quick/predictions.jsonl':run_id=primary_id
  info={'id':run_id,'path':relative,'sha256':sha(path),'manifest':manifest_id,'manifest_source':manifest_path,'manifest_n':len(gs),'settings':settings,'run_metadata_path':str(path.parent/'run.json')if runmeta else None,'run_metadata_sha256':sha(path.parent/'run.json')if runmeta else None,'report_path':str(reportpath.relative_to(ROOT))if reportpath.exists()else None,'report_sha256':sha(reportpath)if reportpath.exists()else None,'mode':mode,'recorded_mode_labels':sorted(modes),'mode_note':'Explicit run mode; targeted/inventory experiments labelled Hybrid despite inherited local label'if 'targeted-'in relative or'pilot'in relative else'Original run mode','mismatches':errors,'duplicates':[],'orphans':[],'recorded':0,'line_count':line_count}
  lookup={g['sample_id']:g for g in gs}
  with path.open('rb')as f:
   while True:
    offset=f.tell();raw=f.readline()
    if not raw:break
    try:p=json.loads(raw)
    except Exception:continue
    id=p.get('sample_id')
    if id not in lookup:info['orphans'].append(id);continue
    g=lookup[id]
    if id in seen:info['duplicates'].append(id);continue
    seen.add(id)
    if p.get('path')!=g['path']or p.get('question')!=g['question']:
     info['mismatches'].append({'id':id,'reason':'path/question mismatch against declared manifest'});continue
    row=make_row(run_id,mode,g,p);row['prediction_file']=relative;row['prediction_offset']=offset;row['prediction_sha256']=hashlib.sha256(raw).hexdigest();c.execute('INSERT INTO predictions VALUES(?,?,?,?,?,?)',(run_id,mode,id,offset,len(raw),json.dumps(row,ensure_ascii=False)));info['recorded']+=1
    if run_id==primary_id:primary.append(row)
  if run_id==primary_id:
   have={r['sample_id']for r in primary};primary +=[make_row(run_id,'local',g,None)for g in gs if g['sample_id']not in have];primary_hybrid=[make_row(run_id,'hybrid',g,None)for g in gs]
  info['not_recorded']=len(gs)-info['recorded'];catalog.append(info);c.execute('INSERT INTO runs VALUES(?,?,?)',(run_id,manifest_id,json.dumps(info,ensure_ascii=False)));c.commit();print(number+1,len(files),run_id,info['recorded'],len(gs),flush=True)
 c.close();temp.replace(DB)
 if len(primary)!=9544:raise AssertionError('Primary manifest reconciliation failed')
 with(OUT/'quick-rows.jsonl').open('w')as f:
  for row in primary+primary_hybrid:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 # Human-readable compact CSV retains question/drawing IDs and orthogonal statuses.
 fields=['run_id','mode','sample_id','drawing_id','path','input_format','dataset','question_type','target','language','outcome','recorded','execution_status','answer_present','grading_status','evidence_availability','evidence_type','replay_availability','ocr_route','ocr_orientation','cache_state','pipeline_seconds','absolute_error','signed_error']
 with(OUT/'quick-rows.csv').open('w')as f:
  writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(primary+primary_hybrid)
 dimensions={'format':['input_format'],'dataset':['dataset'],'question_type':['question_type'],'target':['target'],'route_model':['route','model'],'language':['language'],'evidence':['evidence_availability','evidence_type'],'format_type':['input_format','question_type'],'dataset_target':['dataset','target'],'combination_type':['combination','question_type'],'ocr_format':['ocr_route','input_format'],'ocr_target':['ocr_route','target']};groups={}
 for name,keys in dimensions.items():
  buckets=collections.defaultdict(list)
  for row in primary:buckets[' × '.join(str(row[k])for k in keys)].append(row)
  groups[name]={key:summarize(rows)for key,rows in sorted(buckets.items())}
 for fmt in ['PNG','Other raster','PDF','SVG','IFC','Other']:groups['format'].setdefault(fmt,summarize([]))
 summary={'schema':1,'generated':time.time(),'primary_run':next(r for r in catalog if r['id']==primary_id),'primary_local':summarize(primary),'primary_hybrid_absent':summarize(primary_hybrid),'groups':groups,'runs':catalog,'excluded_collections':excluded,'legacy_replay':{'records':len(legacy_records),'mode_records':len(legacy_assets),'broken_asset_records':sum(bool(r['missing_assets'])for r in legacy_assets),'assets':legacy_assets,'index_source':'results/v2/replay-delivery/index.json','index_sha256':sha(RESULTS_ROOT/'v2/replay-delivery/index.json'),'note':'Original frozen40 v2 paired plus2 separately attributed A0 local examples; not v3 full quick. Default old UI curated20 correct entries; wrong saved outcomes filtered, not absent predictions.'},'numeric_rules':'Existing supplied evaluator, exact integer count; normalized units; area/length/volume2% tolerance, zero absolute1e-9. Text is ungraded. No relative error against zero.','orientation_note':'No recorded OCR-specific orientation correction found; CNN rotation ensembles are not OCR orientation. Orientation intersections N/A unless explicit OCR metadata appears.','definition':'Every run is separate; question manifest LEFT JOIN actual predictions, no backfill from another version. Primary rows include explicit missing Hybrid mode. SQLite holds all discovered compatible saved question-level evaluation results; no inference.'}
 summary['examples']={k:[r['sample_id']for r in primary if r['outcome']==k][:8]for k in OUTCOMES};write_json(OUT/'summary.json',summary);write_json(OUT/'runs.json',catalog);write_report(summary);print('PRIMARY',json.dumps(summary['primary_local']['outcomes']),'index',DB)

def write_report(s):
 def rate(x):return 'N/A'if x is None else f'{100*x:.2f}%'
 def table(groups):
  text='|Group|Questions / drawing groups|Recorded|Answered|Correct|Incorrect|Ungraded|Abstained / unsupported / errors|Not recorded|Coverage|Correct / all scorable|Correct / graded answered|\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
  for k,v in groups.items():text+=f"|{k.replace('|','/')}|{v['total']} / {v['unique_drawings']}|{v['recorded']}|{v['answered']}|{v['correct']}|{v['incorrect']}|{v['answered_ungraded']}|{v['abstained']} / {v['unsupported']} / {v['execution_error']}|{v['not_recorded']}|{rate(v['answer_coverage'])}|{v['correct']}/{v['scorable_n']} ({rate(v['correct_all_scorable'])})|{v['correct']}/{v['graded_answered_n']} ({rate(v['correct_graded_answered'])})|\n"
  return text
 t='# FloorHAWK solution analytics — saved results only\n\nRegenerate: `cd proofplan && .venv/bin/python -m inspection.supervise -- .venv/bin/python -m inspection.analytics`. No model, OCR, orientation or provider calls. Machine summary: results/inspection/summary.json; row-per-question/mode JSONL and CSV: quick-rows.*; all compatible saved runs: index.sqlite3 and runs.json.\n\n'
 p=s['primary_run'];t+=f"Primary quick manifest: **{s['primary_local']['total']} questions / {s['primary_local']['unique_drawings']} unique drawing groups / {s['primary_local']['unique_input_files']} input files**. Reported score comes from **{p['path']}**, mode Local, configuration/source hashes in its run.json and this summary. **{s['primary_local']['correct']}/{s['primary_local']['scorable_n']} ({rate(s['primary_local']['correct_all_scorable'])}) numeric**; text is separate. This is frozen v3 development, not held-out accuracy. No inference was rerun.\n\n"
 t+='## Reconciliation before gallery changes\n\n'+table({'v3 release quick Local':s['primary_local'],'v3 release quick Hybrid (not run)':s['primary_hybrid_absent']})
 lr=s['legacy_replay'];t+=f"\nOriginal replay exports **{lr['records']} questions / {lr['mode_records']} mode records**, with **{lr['broken_asset_records']} records missing required preview/overlay assets**. It is the old v2 paired snapshot plus2 labelled A0 examples, not the9,544-question v3 run. The old default deliberately retained20 curated successful questions and removed wrong/non-correct mode entries. A prediction omitted by export/curation must not be confused with absence. The full-v3 Hybrid run does not exist; do not borrow older Hybrid answers. Failed/abstained predictions are recorded outcomes. New inspection indexes all discovered compatible runs separately and renders source assets on demand. Missing image/overlay assets do not erase the saved answer.\n\n"
 t+='|Saved run|Mode|Manifest|Recorded|Missing|Duplicates|Orphans|Schema/path mismatches|\n|---|---|---:|---:|---:|---:|---:|---:|\n'
 for r in s['runs']:t+=f"|{r['id']}|{r['mode']}|{r['manifest_n']}|{r['recorded']}|{r['not_recorded']}|{len(r['duplicates'])}|{len(r['orphans'])}|{len(r['mismatches'])}|\n"
 t+='\nSource JSONL SHA256, run metadata/config/source hashes, byte offsets and original record hashes are retained; duplicate records are reported, never overwritten/backfilled. Unsupported non-question spatial collections are listed explicitly in excluded_collections. Derived manifest subsets are identified rather than claimed complete quick campaigns.\n\n## Status/denominator definitions\n\nMutually exclusive outcomes: Correct/Incorrect require successful numeric answers and the existing evaluator; Answered but ungraded includes text/unsupported rubric; Abstained/Unsupported preserve those statuses; Execution error includes failed/invalid/success-without-answer; Not recorded means no matched saved prediction. Execution status, answer presence, grade, evidence and replay availability remain separate fields. Coverage=successful non-null answers/all questions. Correct/all scorable includes absent/abstained/unsupported/errors; Correct/graded answered excludes ungraded text and unanswered rows. Zero denominators are N/A. Counts include translations/repeated questions; drawing totals expose weighting.\n\n'
 for name in ['format','dataset','question_type','target','route_model','language','evidence','format_type','dataset_target','combination_type','ocr_format','ocr_target']:
  t+='## '+name.replace('_',' ').title()+' — primary Local only\n\n'+table(s['groups'][name])+'\n'
 t+='## Count and continuous errors\n\n|Quantity|Valid predictions|MAE|Signed bias|Under / over / exact|Relative-error nonzero N|Mean relative error|\n|---|---:|---:|---:|---:|---:|---:|\n'
 for typ,v in s['primary_local']['quantities'].items():t+=f"|{typ}|{v['valid_n']}|{v['mae'] if v['mae']is not None else 'N/A'}|{v['signed_bias'] if v['signed_bias']is not None else 'N/A'}|{v['under_n']} / {v['over_n']} / {v['exact_n']}|{v['relative_nonzero_n']}|{v['mean_relative_error_nonzero']if v['mean_relative_error_nonzero']is not None else'N/A'}|\n"
 t+='\nErrors require valid unit-compatible numeric predictions; missing errors are not zero. Count accuracy is exact; continuous correctness uses the supplied tolerance. Relative errors exclude zero references.\n\n## Timing and OCR observations\n\n'+json.dumps(s['primary_local']['timings'],indent=2)+'\n\nRecorded pipeline timings are split by explicit cache flag; missing/unknown is not uncached, and missing timing is not zero. Cached structural/room stage dictionaries can retain original-generation inference times: these are retained in row metadata, not treated as new inference latency. Comparisons by route are observational, not causal ablations.\n\n'+s['orientation_note']+' Native PDF text extraction is not OCR. Raster/rendered-PDF OCR requires explicit stage/method/warning metadata; untraced baseline OCR is unknown, not inferred from question language.\n\n'
 ranked=sorted(((k,v)for k,v in s['groups']['target'].items()if v['total']>=30),key=lambda x:-(x[1]['incorrect']+x[1]['abstained']+x[1]['unsupported']+x[1]['execution_error']));t+='## Error-heavy targets (at least30 questions)\n\n'+table(dict(ranked))+'\n'
 t+='## Representative IDs\n\n'+ '\n'.join(f'- {k}: '+(', '.join(v)or'N/A')for k,v in s['examples'].items())+'\n\n## Model capability and evidence limits\n\n|Component|Native/direct capability|OCR-supported / derived|Unsupported or caution|\n|---|---|---|---|\n|RT-DETR structural|wall,door,window,railing,linkage_point|class-aware filtering of real boxes|Sauna is not its task; absence of a class does not explain another route failure|\n|CubiCasa|rooms12classes; icons include windows,doors,toilet fixtures,sinks,sauna benches,bathtubs|reconstructed polygons, room context|No dedicated shower output; raw sink class can include faucets|\n|PP-OCR / native PDF text|recorded strings and source regions|labels associate to room geometry|Untraced OCR/orientation unknown; OCR text is not completeness proof|\n|Weak room/washing/layout heads|global count-supervised role weights over observed proposals|sauna/kitchen/bath/WC/balcony roles; coarse washing/floor regions|Counts can match while evidence merges regions; no new spatial GT inferred|\n|IFC / PDF structured tools|GUID occurrences, declared properties/units, labelled areas/schedule quantities|explicit associations/arithmetic|Missing/ambiguous scope abstains; one row may represent many items|\n\nSauna facts: saved routes include native geometry, room fusion and OCR-supported concepts; error labels alone do not establish why. Windows facts: saved structural boxes/filtering and other formats differ; count error cannot identify missed openings. OCR hypotheses (tiny text, orientation, incomplete labels) need trace/spatial evidence; they are not established by a wrong count. SVG inputs are counted only from evaluation path suffixes; training SVG annotations and rendered derivatives never enter those totals. No spatial ground truth is invented or displayed from count references.\n'
 (RESULTS_ROOT/'inspection/HISTORICAL_ANALYTICS.md').write_text(t)
if __name__=='__main__':
 build()
 from .augment import augment
 augment()
 from .reconcile import run
 run()
