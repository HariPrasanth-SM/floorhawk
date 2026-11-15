from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Read-only saved-result repository. References are confined to replay/analytics."""
import base64,json,sqlite3,hashlib,math
from pathlib import Path
from qa.common import ROOT
from . import assets
from .translations import for_question
DB=RESULTS_ROOT/'inspection/index.sqlite3'
def token(run,mode,id):return base64.urlsafe_b64encode(json.dumps([run,mode,id],separators=(',',':')).encode()).decode().rstrip('=')
def decode(value):
 try:items=json.loads(base64.urlsafe_b64decode(value+'='*((-len(value))%4)))
 except Exception:raise ValueError('Invalid saved-result ID')
 if not isinstance(items,list)or len(items)!=3 or any(not isinstance(x,str)or len(x)>200 for x in items)or items[1]not in ['local','hybrid']:raise ValueError('Invalid saved-result ID')
 return items
class Store:
 def __init__(self,db=DB):self.db=Path(db);self.facets_cache={}
 def connect(self):return sqlite3.connect(f'file:{self.db}?mode=ro',uri=True)
 def runs(self):
  with self.connect()as c:runs=[json.loads(x[0])for x in c.execute('SELECT info FROM runs ORDER BY id')]
  pair=self.pair_info()
  if pair:runs.insert(0,pair)
  return runs
 def pair_info(self):
  with self.connect()as c:rows=[c.execute('SELECT info FROM runs WHERE id=?',(id,)).fetchone()for id in ['v3-paired-local','v3-paired-hybrid']]
  if not all(rows):return None
  a,b=[json.loads(r[0])for r in rows];sa=dict(a['settings']);sb=dict(b['settings']);sa.pop('mode',None);sb.pop('mode',None)
  if sa!=sb or a['manifest']!=b['manifest']:return None
  return dict(a,id='v3-frozen40-comparison',label='v3 frozen40 · Local/Hybrid matched configuration',available_modes=['local','hybrid'],paired_sources={'local':a['id'],'hybrid':b['id']},paired=True)
 def info(self,run,mode=None):
  if run=='v3-frozen40-comparison':
   pair=self.pair_info()
   if not pair:raise ValueError('Matched run configurations do not agree')
   actual=self.info(pair['paired_sources'][mode or 'local']);return dict(actual,id=run,component_run_id=actual['id'],paired_sources=pair['paired_sources'])
  with self.connect()as c:r=c.execute('SELECT info FROM runs WHERE id=?',(run,)).fetchone()
  if not r:raise ValueError('Unknown saved run')
  return json.loads(r[0])
 def questions(self,run):
  info=self.info(run)
  with self.connect()as c:return[json.loads(x[0])for x in c.execute('SELECT gold FROM questions WHERE manifest=? ORDER BY id',(info['manifest'],))]
 def facets(self,run):
  if run in self.facets_cache:return self.facets_cache[run]
  from .analytics import format_of,CATEGORY_TARGET
  qs=self.questions(run);result={'formats':sorted({format_of(q['path'])for q in qs}),'datasets':sorted({q.get('source','unknown')for q in qs}),'targets':sorted({CATEGORY_TARGET.get(q.get('category'))or q.get('category','unknown')for q in qs}),'total_questions':len(qs)};self.facets_cache[run]=result;return result
 def cases(self,run,mode='local',outcome='all',datatype='',dataset='',target='',page=0,limit=80):
  from .analytics import format_of,CATEGORY_TARGET
  if mode not in ['local','hybrid']:raise ValueError('Unknown mode')
  info=self.info(run,mode);qs=self.questions(run)
  with self.connect()as c:pred={id:json.loads(row)for id,row in c.execute('SELECT id,row FROM predictions WHERE run=? AND mode=?',(info.get('component_run_id',run),mode))}
  rows=[]
  for q in qs:
   id=q['sample_id'];r=pred.get(id);label=r['outcome']if r else'Not recorded';fmt=format_of(q['path']);tar=CATEGORY_TARGET.get(q.get('category'))or q.get('category','unknown')
   if datatype and datatype!=fmt or dataset and dataset!=q.get('source','unknown')or target and target!=tar:continue
   if outcome=='correct'and label!='Correct'or outcome=='failed'and label not in ['Incorrect','Abstained','Unsupported','Execution error']or outcome=='missing'and label!='Not recorded'or outcome=='ungraded'and label!='Answered but ungraded':continue
   rows.append({'id':token(run,mode,id),'sample_id':id,'question':q['question'],'path':q['path'],'outcome':label,'execution_status':r['execution_status']if r else'not_recorded','format':fmt,'dataset':q.get('source'),'target':tar,'evidence_availability':r['evidence_availability']if r else'no_prediction','recorded':r is not None})
  page=max(0,int(page));limit=max(1,min(100,int(limit)));total=len(rows);last=max(0,(total-1)//limit);page=min(page,last);return{'cases':rows[page*limit:(page+1)*limit],'total':total,'page':page,'pages':last+1,'limit':limit,'run':run,'mode':mode,'recorded_mode':info['mode'],'note':'No borrowing predictions from another run/version.'}
 def lookup(self,ident):
  run,mode,id=decode(ident);info=self.info(run,mode)
  with self.connect()as c:
   q=c.execute('SELECT gold FROM questions WHERE manifest=? AND id=?',(info['manifest'],id)).fetchone();p=c.execute('SELECT offset,length,row FROM predictions WHERE run=? AND mode=? AND id=?',(info.get('component_run_id',run),mode,id)).fetchone()
  if not q:raise ValueError('Question outside selected manifest')
  gold=json.loads(q[0]);row=json.loads(p[2])if p else None;pred=None
  if p:
   source=(ROOT/info['path']).resolve()
   if not source.is_relative_to((RESULTS_ROOT).resolve()):raise ValueError('Unsafe registered source')
   try:
    with source.open('rb')as f:f.seek(p[0]);raw=f.read(p[1])
    if hashlib.sha256(raw).hexdigest()!=row['prediction_sha256']:raise ValueError('Indexed record integrity mismatch')
    pred=json.loads(raw)
   except (OSError,ValueError):pred={'status':row['execution_status'],'answer':row['answer'],'unit':row['unit'],'evidence':[],'route':row['route'],'model':{'name':row['model']},'warnings':['Original prediction record unavailable or changed; indexed saved answer retained, evidence unavailable.'],'timing':{'total_seconds':row['pipeline_seconds']or 0},'task':{'operation':gold['type'],'target':row['target']},'indexed_snapshot_only':True}
  return info,gold,row,pred
 def source(self,ident):
  _,gold,_,_=self.lookup(ident);source=(DATASET_ROOT/gold['path']).resolve()
  if not source.is_relative_to((DATASET_ROOT).resolve()):raise ValueError('Unsafe dataset path')
  return source
 def job(self,ident):
  info,g,row,pred=self.lookup(ident);source=self.source(ident);missing=pred is None
  if pred is None:pred={'status':'not_recorded','answer':None,'unit':g.get('unit'),'evidence':[],'route':'not recorded','warnings':[f"No saved {decode(ident)[1].title()} prediction exists for this question in selected run {info['id']}."],'timing':{'total_seconds':0},'task':{'operation':g['type'],'target':g.get('category')},'model':{'name':'No prediction'}}
  pred=dict(pred);pred.setdefault('evidence',[]);pred.setdefault('warnings',[]);pred.setdefault('timing',{'total_seconds':0});pred.setdefault('device','not recorded');pred.setdefault('model',{'name':'not recorded'})
  try:pages=assets.page_info(source);boxes=assets.boxes_for(pred,pages,source)
  except Exception:
   pages=[{'page':1,'width':1000,'height':600,'scale':1}];boxes=[];pred['warnings']=list(pred['warnings'])+['Source preview cannot be rendered; saved answer retained.']
  suffix=source.suffix.lower();kind='pdf'if suffix=='.pdf'else'ifc'if suffix=='.ifc'else'image';credit='CubiCasa5K; Kalervo et al.2019; source drawing attribution retained; CC BY-NC-SA4.0'if'cubicasa5k/'in g['path']else'Swiss Dwellings/Archilyse CC BY4.0; original drawing credit retained'if'swiss_dwellings/'in g['path']else'Original source attribution/licence: '+str(Path(g['path']).parent/'LICENSE.md');grade={'passed':True if row and row['outcome']=='Correct'else None if row and row['outcome']=='Answered but ungraded'else False,'reason':row['grade_reason']if row else'not recorded'};trace=pred.get('calculation_trace',[]);instances=any(t.get('operation')=='count_unique_included_entities'for t in trace)
  return {'id':ident,'status':'success','stage':'Saved result inspection, no inference','input_kind':kind,'source_name':g['path'],'source_sha256':pred.get('source_sha256'),'credit':credit,'question':g['question'],'pages':pages,'image_size':[pages[0]['width'],pages[0]['height']],'prediction':pred,'review':{'revision':0,'boxes':boxes,'included_evidence_ids':[e.get('id')for e in pred['evidence']if e.get('id')],'reviewed_count':len(boxes)if kind!='ifc'else len(pred['evidence']),'answer':pred.get('answer'),'unit':pred.get('unit'),'reviewed':False,'instance_count':instances},'replay':{'expected':g['answer'],'unit':g.get('unit'),'grade':grade,'outcome':row['outcome']if row else'Not recorded','question_type':g['type'],'signed_error':row.get('signed_error')if row else None,'evaluation_label':f"Run {info['id']} · {decode(ident)[1]}; saved development/evaluation artifacts, no inference",'run_id':info['id'],'mode':decode(ident)[1],'original_compute_seconds':pred['timing'].get('total_seconds')or 0,'original_cloud_generation_seconds':pred.get('cloud',{}).get('original_generation',{}).get('timing_seconds'),'source_predictions_sha256':info['sha256'],'source_run_metadata_sha256':info.get('run_metadata_sha256'),'evidence_availability':row['evidence_availability']if row else'no_prediction','source_available':source.is_file(),'missing_recording':missing},'high_resolution_evidence':True,'english_translation':for_question(g)}

 def curated(self,run,mode):
  rows=self.cases(run,mode,limit=100)['cases'];info=self.info(run,mode)
  with self.connect()as c:allrows=[json.loads(r[0])for r in c.execute('SELECT row FROM predictions WHERE run=? AND mode=? ORDER BY id',(info.get('component_run_id',run),mode))]
  buckets={};order={'Correct':0,'Incorrect':1,'Abstained':2,'Unsupported':3,'Execution error':4,'Answered but ungraded':5}
  for row in sorted(allrows,key=lambda r:r['sample_id']):buckets.setdefault((row['input_format'],row['outcome'],row['question_type']),row)
  formats=sorted({k[0]for k in buckets},key=lambda f:['PNG','PDF','IFC','SVG'].index(f)if f in['PNG','PDF','IFC','SVG']else 99);byformat={f:sorted([r for (fmt,_,_),r in buckets.items()if fmt==f],key=lambda r:(order.get(r['outcome'],9),r['question_type']))for f in formats};chosen=[]
  while len(chosen)<16 and any(byformat.values()):
   for fmt in formats:
    if not byformat[fmt]or len(chosen)>=16:continue
    row=byformat[fmt].pop(0);chosen.append({'id':token(run,mode,row['sample_id']),'sample_id':row['sample_id'],'label':' · '.join([row['input_format'],row['outcome'],row['question_type'],row['sample_id']])})
  return{'cases':chosen,'note':'Small starting collection across available formats/tasks/outcomes; filters/pagination expose every question. No fabricated fillers.'}
