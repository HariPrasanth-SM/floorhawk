from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Extend the existing FloorHAWK review server with the shared QA pipeline."""
import argparse,base64,io,json,time,uuid,math,os
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageOps,ImageDraw
from legacy_server import Application as ReviewApplication,Handler as ReviewHandler,STORE,ThreadingHTTPServer
from qa.common import ROOT,sha,write_json
if os.environ.get('PROOFPLAN_RELEASE')=='v3':
 from v3.pipeline import Pipeline
else:
 from v2.pipeline import Pipeline
from detector import render,validate_boxes
from image_ingest import prepare

class Application(ReviewApplication):
 def __init__(self,device,max_edge=512,vlm_url=None):
  from demo_gpu import install
  install()
  super().__init__(device,'baseline');self.pipeline=Pipeline(device,max_edge,vlm_url);self.vlm_url=vlm_url;self.paired=None
  if os.environ.get('PROOFPLAN_PAIRED')=='1':
   from iteration.paired import Engine
   self.paired=Engine(self.pipeline)
  self.large=None
  if os.environ.get('PROOFPLAN_LARGE_DRAWINGS')=='1':
   from large_drawing import LargeDrawing
   self.large=LargeDrawing(self.paired)
 def admission_busy(self):
  return any(j['status'] in ('queued','running') for j in self.jobs.values())
 def create(self,body):
  submitted=time.perf_counter()
  with self.guard:
   if self.admission_busy():raise ValueError('The local worker is busy. Wait for the current question to finish.')
  mode=body.get('mode','local')
  if mode not in ('local','hybrid'):raise ValueError('Choose local or hybrid mode')
  question=body.get('question','')
  if not isinstance(question,str) or not question.strip() or len(question)>4000:raise ValueError('Enter a natural-language question (up to 4000 characters).')
  credit=body.get('credit') or 'User-supplied file; attribution not provided'
  if not isinstance(credit,str) or len(credit)>1000:raise ValueError('Invalid attribution')
  if 'sample' in body:
   row=next((r for r in self.samples if r['id']==body['sample']),None)
   if row is None:raise ValueError('Unknown demo')
   source=DATASET_ROOT/row['image'];data=source.read_bytes();suffix=source.suffix;credit=row['credit']
  else:
   name=body.get('file_name','upload.png');suffix=Path(name).suffix.lower()
   if suffix not in ('.png','.jpg','.jpeg','.pdf','.ifc'):raise ValueError('Upload PNG, JPEG, PDF or IFC.')
   try:data=base64.b64decode(body.get('file_base64',''),validate=True)
   except Exception:raise ValueError('Invalid file encoding')
  if not data or len(data)>100*1024**2:raise ValueError('Use a nonempty file under 100 MB (images under 20 MB).')
  ident=uuid.uuid4().hex;dest=STORE/ident;dest.mkdir();source=dest/('source'+suffix);source.write_bytes(data)
  pages=[];ingestion=None;canonical_source=None
  try:
   if suffix in ('.png','.jpg','.jpeg'):
    if len(data)>20*1024**2:raise ValueError('Images must be under 20 MB.')
    im,ingestion=prepare(data);canonical_source='image.png'
    im.save(dest/'image.png');pages=[{'page':1,'width':im.width,'height':im.height,'coordinate_system':'EXIF-normalized working image pixels; ingestion transform maps to original'}];kind='image'
   elif suffix=='.pdf':
    import pymupdf
    with pymupdf.open(source) as doc:
     if doc.is_encrypted:raise ValueError('Password-protected PDF is unsupported.')
     if len(doc)>100:raise ValueError('Use a PDF with at most 100 pages.')
     for pn,page in enumerate(doc):
      scale=1400/max(page.rect.width,page.rect.height);pages.append({'page':pn+1,'width':math.ceil(page.rect.width*scale),'height':math.ceil(page.rect.height*scale),'scale':scale,'rotation':page.rotation,'coordinate_system':'displayed PDF page pixels; source evidence retains unrotated PDF points'})
     doc[0].get_pixmap(matrix=pymupdf.Matrix(pages[0]['scale'],pages[0]['scale']),alpha=False).save(dest/'image.png')
    kind='pdf'
   else:
    if b'ISO-10303-21' not in data[:2000]:raise ValueError('Use an IFC STEP file (ISO-10303-21), not a screenshot or IFCZIP.')
    im=Image.new('RGB',(800,450),'#f2f5ef');draw=ImageDraw.Draw(im);draw.text((40,160),'IFC MODEL\nEvidence is shown by GUID and property below.\nThis preview is not a rendered model.',fill='black');im.save(dest/'image.png');pages=[{'page':1,'width':800,'height':450,'coordinate_system':'no spatial image evidence for IFC'}];kind='ifc'
  except Exception as exc:raise ValueError('File validation failed: '+str(exc))
  job={'id':ident,'status':'queued','stage':'Waiting for shared local worker','progress':0,'device':self.detector.device,'credit':credit,'question':question,'mode':mode,'source_name':body.get('file_name',body.get('sample','demo')),'source_file':source.name,'source_sha256':sha(source),'input_kind':kind,'image_size':[pages[0]['width'],pages[0]['height']],'pages':pages,'created':time.time(),'_submitted_perf':submitted}
  if ingestion:job.update(ingestion_transform=ingestion,canonical_source_file=canonical_source)
  with self.guard:self.jobs[ident]=job
  write_json(dest/'job.json',job)
  self.worker.submit(self.execute,ident);return {'id':ident}
 def get(self,ident):
  already_live=ident in self.jobs;job=super().get(ident)
  if 'source_file' not in job:raise ValueError('This is an archived v1 window review. Its original exports remain in results/app; upload the drawing for the current QA workflow.')
  if not already_live and job['status'] in ('queued','running'):
   job.update(status='failed',stage='Previous server stopped during this job',error='The previous server stopped before completion. Re-upload the retained source file and retry; no answer was substituted.')
   write_json(STORE/ident/'job.json',job)
  return job
 def preview(self,job,page=1):
  if page<1 or page>len(job['pages']):raise ValueError('Unknown PDF page')
  dest=STORE/job['id'];target=dest/('image.png' if page==1 else f'page-{page}.png')
  if not target.exists():
   import pymupdf
   with pymupdf.open(dest/job['source_file']) as doc:doc[page-1].get_pixmap(matrix=pymupdf.Matrix(job['pages'][page-1]['scale'],job['pages'][page-1]['scale']),alpha=False).save(target)
  return target
 def view_boxes(self,job,pred):
  boxes=[]
  if job['input_kind']=='ifc':return boxes
  import pymupdf
  doc=pymupdf.open(STORE/job['id']/job['source_file']) if job['input_kind']=='pdf' else None
  for e in pred.get('evidence',[]):
   if 'bbox' not in e:continue
   pn=e.get('page',1);b=e['bbox']
   if pred.get('coordinate_system')=='original_exif_normalized_pixels'and job.get('ingestion_transform'):
    info=job['ingestion_transform'];ow,oh=info['raw_size'];ow,oh=(oh,ow)if info['exif_orientation']in[5,6,7,8]else(ow,oh);cw,ch=info['canonical_size'];b=[b[0]*cw/ow,b[1]*ch/oh,b[2]*cw/ow,b[3]*ch/oh]
   if doc is not None:
    rect=pymupdf.Rect(b)*doc[pn-1].rotation_matrix*pymupdf.Matrix(job['pages'][pn-1]['scale'],job['pages'][pn-1]['scale']);b=list(rect)
   w,h=job['pages'][pn-1]['width'],job['pages'][pn-1]['height'];b=[max(0,min(w,b[0])),max(0,min(h,b[1])),max(0,min(w,b[2])),max(0,min(h,b[3]))]
   if b[0]<b[2] and b[1]<b[3]:boxes.append({'xyxy':b,'page':pn,'included':True,'detector_score':e.get('score'),'evidence_id':e['id'],'class_name':e.get('class',e.get('kind','evidence'))})
  if doc is not None:doc.close()
  return boxes
 def execute(self,ident):
  job=self.jobs[ident];dest=STORE/ident
  def progress(stage,current,total):
   with self.guard:job.update(status='running',stage=stage,progress=current/total)
  try:
   from demo_gpu import _last
   _last.clear()
   progress('Reading the supplied file and question',0,1)
   def local_ready(local):
    write_json(dest/'predictions.local.json',local);boxes=self.view_boxes(job,local);instances=any(t.get('operation')=='count_unique_included_entities'for t in local.get('calculation_trace',[]))or(local.get('task',{}).get('operation')=='count'and local['status']!='success'and local.get('coverage',{}).get('complete')is not False);review={'revision':0,'boxes':boxes,'included_evidence_ids':[e['id']for e in local.get('evidence',[])],'reviewed_count':len(boxes),'answer':local.get('answer'),'unit':local.get('unit'),'reviewed':False,'instance_count':instances}
    job.update(local_prediction=local,local_review=review,stage='Local answer saved; waiting for separate Hybrid answer');write_json(dest/'job.json',job)
   if self.large and job.get('ingestion_transform',{}).get('resized'):
    result=self.large.answer(dest/job['source_file'],job['question'],mode=job.get('mode','local'),on_local=local_ready,progress=progress)
    if result.get('paired'):write_json(dest/'predictions.hybrid.json',result['paired']['hybrid'])
   elif self.paired:
    result=self.paired.answer(dest/job.get('canonical_source_file',job['source_file']),job['question'],sample_id=None,progress=progress,mode=job.get('mode','local'),on_local=local_ready)
    if result.get('paired'):write_json(dest/'predictions.hybrid.json',result['paired']['hybrid'])
   else:
    result=self.pipeline.answer(dest/job.get('canonical_source_file',job['source_file']),job['question'],sample_id=None,progress=progress,mode=job.get('mode','local'))
   if job.get('ingestion_transform',{}).get('resized'):result.setdefault('warnings',[]).insert(0,'Large upload resized from '+str(job['ingestion_transform']['raw_size'])+' to '+str(job['ingestion_transform']['canonical_size'])+' pixels for bounded local processing. Original file retained; fine text/symbols may be less readable.')
   if job.get('ingestion_transform'):result.update(upload_source_sha256=job['source_sha256'],ingestion_transform=job['ingestion_transform'])
   from demo_gpu import _last
   events={}
   for item in _last:
    key=(item.get('model'),item.get('gpu_before',{}).get('time'),item.get('fallback_reason'))
    if key not in events or not item.get('cache_hit'):events[key]=item
   result['live_execution']=result.get('live_execution',[])+list(events.values());_last.clear()
   if result['live_execution']:result['device']=result['live_execution'][-1]['device']
   result['request_id']=ident;result['application_source_sha256']={name:sha(ROOT/name) for name in ['qa_app.py','web/app.js','web/index.html']};result['application_seconds']=time.perf_counter()-job.pop('_submitted_perf')
   write_json(dest/'predictions.json',result)
   if result['status']=='failed':raise RuntimeError(result.get('error','Question answering failed'))
   boxes=self.view_boxes(job,result);is_count=result.get('task',{}).get('operation')=='count';instances=any(t.get('operation')=='count_unique_included_entities' for t in result.get('calculation_trace',[])) or (is_count and result['status']!='success'and result.get('coverage',{}).get('complete')is not False)
   review={'revision':0,'boxes':boxes,'included_evidence_ids':[e['id'] for e in result['evidence']],'reviewed_count':len(boxes) if job['input_kind']!='ifc' else len(result['evidence']),'answer':result['answer'],'unit':result['unit'] or result.get('task',{}).get('requested_unit'),'reviewed':False,'instance_count':instances}
   job.update(status='success',stage='Answer ready; inspect status and evidence',progress=1,prediction=result,review=review)
  except Exception as exc:job.update(status='failed',stage='Question answering failed',error=str(exc),progress=0)
  write_json(dest/'job.json',job)
 def review(self,ident,body):
  with self.guard:
   job=self.get(ident)
   if job['status']!='success':raise ValueError('Wait for the answer before reviewing')
   if body.get('base_revision')!=job['review']['revision']:raise ValueError('Review changed; reload the drawing before saving')
   boxes=[]
   for b in body.get('boxes',[]):
    page=b.get('page',1)
    if not isinstance(page,int) or not 1<=page<=len(job['pages']):raise ValueError('Invalid review page')
    p=job['pages'][page-1];clean=validate_boxes([b],p['width'],p['height'])[0];clean.update(page=page,evidence_id=b.get('evidence_id'),class_name=b.get('class_name','human_evidence'));boxes.append(clean)
   included=body.get('included_evidence_ids',job['review']['included_evidence_ids']);valid={e['id'] for e in job['prediction']['evidence']}
   if not isinstance(included,list) or any(not isinstance(x,str) or x not in valid for x in included) or len(set(included))!=len(included):raise ValueError('Invalid evidence identifiers')
   count=sum(b['included'] for b in boxes) if job['input_kind']!='ifc' else len(included)
   answer=count if job['review']['instance_count'] else body.get('answer',job['review']['answer'])
   if isinstance(answer,(float,int)) and not math.isfinite(answer):raise ValueError('Review answer must be finite')
   if not isinstance(answer,(str,int,float,type(None))) or (isinstance(answer,str) and len(answer)>10000):raise ValueError('Invalid reviewed answer')
   rev=job['review']['revision']+1;record={'revision':rev,'boxes':boxes,'included_evidence_ids':included,'reviewed_count':count,'answer':answer,'unit':body.get('unit',job['review']['unit']),'reviewed':True,'instance_count':job['review']['instance_count'],'saved_at':time.time(),'predictions_sha256':sha(STORE/ident/'predictions.json')}
   write_json(STORE/ident/f'review-{rev:04d}.json',record);job['review']=record;write_json(STORE/ident/'job.json',job);return record

class Handler(ReviewHandler):
 def do_GET(self):
  if not self.valid_host():return self.send({'error':'Use localhost'},403)
  path=urlparse(self.path).path;app=self.server.app
  try:
   if path.startswith('/vendor/') or path=='/ifc-viewer.js':
    name=path.lstrip('/')
    allowed={'vendor/three.module.js','vendor/OrbitControls.js','vendor/GLTFLoader.js','vendor/BufferGeometryUtils.js','ifc-viewer.js'}
    if name not in allowed:raise ValueError('Unknown viewer asset')
    return self.send((ROOT/'web'/name).read_bytes(),mime='text/javascript')
   if path=='/api/budget':
    from v2.budget import Ledger
    return self.send(Ledger().summary())
   if path in ('/health','/api/config'):
    try:
     from v2.worker_client import request as worker_health
     worker_state=worker_health(timeout=2);health=worker_state['worker']
    except Exception:health={'ready':False,'status':'unavailable','note':'Optional host interpretation worker unavailable; supported local tools remain enabled'}
    data={'ready':True,'paired':app.paired is not None,'device':app.detector.device,'pipeline':'proofplan-v3' if os.environ.get('PROOFPLAN_RELEASE')=='v3' else 'proofplan-v2','model':'Official CubiCasa5K / PyMuPDF / IfcOpenShell','vlm':health,'floorcad_default':False,'token':app.token,'samples':[{'id':r['id'],'credit':r['credit']} for r in app.samples]}
    data['diagnostics']=os.environ.get('PROOFPLAN_DIAGNOSTICS')=='1'
    data['host_vision']=locals().get('worker_state',{}).get('vision',False)
    data['cloud']={'enabled':app.pipeline.cloud_enabled,'default_mode':os.environ.get('PROOFPLAN_DEFAULT_MODE','local'),'server_only':True}
    from v2.budget import Ledger
    data['cloud']['budget']=Ledger().summary()
    if path=='/health':data.pop('token',None)
    return self.send(data)
   if path.startswith('/qa-gallery/'):
    gallery=RESULTS_ROOT/'qa-gallery.json';data=json.loads(gallery.read_text());key=unquote(path[len('/qa-gallery/'):]);allowed={sample.get('overlay') for report in data.get('reports',[]) for sample in report.get('samples',[]) if sample.get('overlay')}
    target=(ROOT/key).resolve()
    if key not in allowed or not target.is_relative_to((RESULTS_ROOT).resolve()) or target.suffix.lower()!='.png':raise ValueError('Unknown registered QA overlay')
    return self.send(target.read_bytes(),mime='image/png')
   if path=='/api/qa-evaluation':
    f=RESULTS_ROOT/'qa-gallery.json';return self.send(json.loads(f.read_text()) if f.exists() else {'reports':[],'note':'No offline QA reports yet.'})
   if path.startswith('/api/jobs/'):
    parts=path.split('/');ident=parts[3];job=app.get(ident);action=parts[4] if len(parts)>4 else ''
    if action in ('crop.png','crop.json','model','model.glb'):
     from inspection import assets
     source=STORE/ident/job.get('canonical_source_file',job['source_file'])
     params=parse_qs(urlparse(self.path).query)
     if action.startswith('crop.'):
      pn=int(params.get('page',['1'])[0]);box=[float(x) for x in params.get('bbox',[''])[0].split(',')]
      if not 1<=pn<=len(job['pages']):raise ValueError('Unknown page')
      preview_page=job['pages'][pn-1]
      if job['input_kind']=='image'and job.get('ingestion_transform'):
       source=STORE/ident/job['source_file'];info=job['ingestion_transform'];rw,rh=info['raw_size'];ow,oh=(rh,rw)if info['exif_orientation']in[5,6,7,8]else(rw,rh);cw,ch=info['canonical_size'];box=[box[0]*ow/cw,box[1]*oh/ch,box[2]*ow/cw,box[3]*oh/ch];preview_page={'width':ow,'height':oh,'scale':1}
      file,metadata=assets.crop(source,pn,box,preview_page);return self.send(metadata if action=='crop.json' else file.read_bytes(),mime='application/json' if action=='crop.json' else 'image/png')
     if job['input_kind']!='ifc':raise ValueError('Not an IFC source')
     from inspection.geometry_jobs import JOBS
     from inspection.ifc_geometry import CACHE,key
     metadata=JOBS.status(source,start=params.get('start',['0'])[0]=='1')
     if action=='model.glb':
      file=CACHE/key(source)/'model.glb'
      if not file.exists():raise ValueError('IFC geometry not ready')
      return self.send(file.read_bytes(),mime='model/gltf-binary')
     metadata['glb_url']=f'/api/jobs/{ident}/model.glb';return self.send(metadata)
    if action=='page' and len(parts)==6:return self.send(app.preview(job,int(parts[5])).read_bytes(),mime='image/png')
    if action=='presentation':
     from presentation import selected
     mode=parse_qs(urlparse(self.path).query).get('mode',['local'])[0];evidence=selected(job,mode)
     pred=dict(job['prediction'],evidence=evidence)
     return self.send({'evidence':evidence,'boxes':app.view_boxes(job,pred),'mode':mode})
    if action=='diagnostic.zip':
     from diagnostic_export import build_archive
     source=STORE/ident/job['source_file'];export_job=dict(job);from presentation import catalog,selected
     export_job['evidence_catalog']=list(catalog(job).values());export_job['hybrid_evidence']=selected(job,'hybrid');export_job['hybrid_view_boxes']=app.view_boxes(job,dict(job['prediction'],evidence=selected(job,'hybrid')));archive=build_archive(export_job,source,app.preview(job,1),STORE/ident/'diagnostic-export');return self.send(archive.read_bytes(),mime='application/zip',download='floorhawk-'+uuid.uuid4().hex[:12]+'.zip')
    if action=='export.json':return self.send({'original_prediction':job.get('prediction'),'human_review':job.get('review'),'source_sha256':job['source_sha256'],'credit':job['credit'],'pages':job['pages']},download='proofplan-answer-review.json')
    if action=='export.png':
     page=int(parse_qs(urlparse(self.path).query).get('page',['1'])[0]);image=app.preview(job,page);target=STORE/ident/f"review-{job['review']['revision']:04d}-page-{page}.png";boxes=[b for b in job['review']['boxes'] if b.get('page',1)==page]
     if not target.exists():render(image,boxes,target,job['credit'],'Human review evidence' if job['review']['reviewed'] else 'Model/tool evidence')
     return self.send(target.read_bytes(),mime='image/png',download=f'proofplan-evidence-page-{page}.png')
   return super().do_GET()
  except (ValueError,KeyError,FileNotFoundError) as exc:return self.send({'error':str(exc)},400)
 def do_POST(self):
  app=self.server.app
  if not self.valid_host() or self.headers.get('X-ProofPlan-Token')!=app.token:return self.send({'error':'Reload the local app before submitting'},403)
  origin=self.headers.get('Origin')
  if origin and origin not in (f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}'):return self.send({'error':'Cross-origin requests disabled'},403)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<=0 or length>140*1024**2:raise ValueError('Request is too large; use a file under 100 MB')
   body=json.loads(self.rfile.read(length));path=urlparse(self.path).path
   if not isinstance(body,dict):raise ValueError('Expected JSON object')
   if path=='/api/cloud-state':
    if set(body)!={'enabled'} or not isinstance(body['enabled'],bool):raise ValueError('Expected enabled boolean')
    app.pipeline.set_cloud(body['enabled']);return self.send({'enabled':body['enabled'],'note':'Disabling stops future admissions. An already transmitted request may finish and stays in the ledger.'})
   if path.startswith('/api/jobs/') and path.endswith('/model-cancel'):
    ident=path.split('/')[3];job=app.get(ident)
    from inspection.geometry_jobs import JOBS
    return self.send(JOBS.cancel(STORE/ident/job['source_file']))
   if path=='/api/jobs':
    if set(body)-{'file_base64','file_name','question','credit','sample','mode'}:raise ValueError('Upload accepts only file, question and attribution fields; no gold metadata')
    return self.send(app.create(body),202)
   parts=path.split('/')
   if len(parts)==5 and parts[1:3]==['api','jobs'] and parts[4]=='review':return self.send(app.review(parts[3],body))
   return self.send({'error':'Not found'},404)
  except (ValueError,TypeError,KeyError) as exc:return self.send({'error':str(exc)},400)

def main():
 p=argparse.ArgumentParser();p.add_argument('--device',choices=['cpu','0'],default='cpu');p.add_argument('--port',type=int,default=8765);p.add_argument('--max-edge',type=int,default=512);p.add_argument('--vlm-url');a=p.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.app=Application(a.device,a.max_edge,a.vlm_url)
 print(f'FloorHAWK QA: http://127.0.0.1:{a.port} | CPU structured tools; vision=host-auto (actual device recorded per job) | FloorCAD disabled as default',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close();server.app.worker.shutdown(wait=True)
if __name__=='__main__':main()
