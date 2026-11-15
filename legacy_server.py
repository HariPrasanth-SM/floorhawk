from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""FloorHAWK local server. Inference routes accept images/settings, never evaluation answers."""
import argparse,base64,concurrent.futures,io,json,mimetypes,secrets,threading,time,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image,ImageOps
from detector import ROOT,Detector,render,validate_boxes,sha
STORE=RESULTS_ROOT/'app';STATIC=ROOT/'web'
Image.MAX_IMAGE_PIXELS=30_000_000

class Application:
 def __init__(self,device,profile):
  self.detector=Detector(device);self.profile=profile;self.profiles=json.loads((ROOT/'profiles.json').read_text());self.worker=concurrent.futures.ThreadPoolExecutor(max_workers=1);self.jobs={};self.guard=threading.RLock();self.token=secrets.token_urlsafe(32)
  STORE.mkdir(parents=True,exist_ok=True)
  self.samples=json.loads((ROOT/'config/demo-samples.json').read_text())
 def create(self,body):
  submitted=time.perf_counter()
  with self.guard:
   if any(j['status'] in ('queued','running') for j in self.jobs.values()):raise ValueError('The local worker is busy. Wait for the current drawing to finish.')
  profile=body.get('profile',self.profile)
  if profile not in ('baseline','hires','tiled'):raise ValueError('Unsupported inference profile')
  if body.get('task','count_windows')!='count_windows':raise ValueError('Only count_windows is supported')
  credit=body.get('credit','User-supplied drawing; attribution not provided')
  if not isinstance(credit,str) or len(credit)>1000:raise ValueError('Attribution must be text under 1000 characters')
  demo=body.get('sample')
  if demo is not None:
   row=next((r for r in self.samples if r['id']==demo),None)
   if not row:raise ValueError('Unknown demo sample')
   data=(DATASET_ROOT/row['image']).read_bytes();credit=row['credit']
  else:
   if not isinstance(body.get('image_base64'),str):raise ValueError('Upload a PNG or JPEG image')
   try:data=base64.b64decode(body['image_base64'],validate=True)
   except Exception:raise ValueError('Invalid image encoding')
  if len(data)>20*1024*1024:raise ValueError('Image exceeds 20 MB. Resize or compress it and retry.')
  try:
   im=Image.open(io.BytesIO(data))
   if im.format not in ('PNG','JPEG'):raise ValueError('Use a PNG or JPEG image')
   im=ImageOps.exif_transpose(im).convert('RGB');im.load()
   if min(im.size)<16 or max(im.size)>16000 or im.width*im.height>30_000_000:raise ValueError('Use images between 16 pixels and 30 megapixels, with edges under 16000 pixels.')
  except (Image.DecompressionBombError,Image.DecompressionBombWarning):raise ValueError('Image is too large to decode safely; resize it first.')
  except ValueError:raise
  except Exception:raise ValueError('Image could not be decoded. Re-export as PNG or JPEG.')
  ident=uuid.uuid4().hex;dest=STORE/ident;dest.mkdir();(dest/'upload.original').write_bytes(data);im.save(dest/'image.png')
  job={'id':ident,'status':'queued','stage':'Waiting for local worker','progress':0,'profile':profile,'device':self.detector.device,'credit':credit,'image_size':list(im.size),'created':time.time(),'_submitted_perf':submitted}
  with self.guard:self.jobs[ident]=job
  self.worker.submit(self.execute,ident)
  return {'id':ident}
 def execute(self,ident):
  job=self.jobs[ident];dest=STORE/ident;started=time.perf_counter()
  def progress(stage,current,total):
   with self.guard:job.update(status='running',stage=stage,progress=current/total)
  try:
   with self.guard:job.update(status='running',stage='Preparing local inference')
   pred=self.detector.predict(dest/'image.png',self.profiles[job['profile']],job['credit'],progress)
   pred['application_source_sha256']={name:sha(ROOT/name) for name in ['app.py','web/index.html','web/app.js','web/style.css']}
   if pred['status']!='success':
    (dest/'predictions.json').write_text(json.dumps(pred,indent=2)+'\n')
    raise RuntimeError(pred['error'])
   render(dest/'image.png',pred['boxes'],dest/'model-overlay.png',job['credit'])
   pred['application_seconds']=time.perf_counter()-started
   pred['request_to_ready_seconds']=time.perf_counter()-job.pop('_submitted_perf',started)
   (dest/'predictions.json').write_text(json.dumps(pred,indent=2)+'\n')
   with self.guard:job.update(status='success',stage='Ready for review',progress=1,prediction=pred,review={'revision':0,'boxes':pred['boxes'],'reviewed_count':len(pred['boxes']),'reviewed':False})
  except Exception as exc:
   with self.guard:job.update(status='failed',stage='Inference failed',error=str(exc),progress=0)
  (dest/'job.json').write_text(json.dumps(job,indent=2)+'\n')
 def get(self,ident):
  if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('Invalid drawing ID')
  with self.guard:
   if ident not in self.jobs:
    path=STORE/ident/'job.json'
    if not path.exists():raise ValueError('Drawing not found')
    self.jobs[ident]=json.loads(path.read_text())
   return self.jobs[ident]
 def review(self,ident,body):
  with self.guard:
   job=self.get(ident)
   if job['status']!='success':raise ValueError('Wait for successful inference before editing')
   if body.get('base_revision')!=job['review']['revision']:raise ValueError('Review changed elsewhere. Reload this drawing before saving.')
   boxes=validate_boxes(body.get('boxes'),*job['image_size']);rev=job['review']['revision']+1
   record={'revision':rev,'boxes':boxes,'reviewed_count':sum(b['included'] for b in boxes),'reviewed':True,'saved_at':time.time(),'predictions_sha256':sha(STORE/ident/'predictions.json')}
   path=STORE/ident/f'review-{rev:04d}.json';path.write_text(json.dumps(record,indent=2)+'\n')
   job['review']=record;(STORE/ident/'job.json').write_text(json.dumps(job,indent=2)+'\n');return record

class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):pass
 def send(self,data,status=200,mime='application/json',download=None):
  if not isinstance(data,bytes):data=json.dumps(data).encode()
  self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'")
  if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
  self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass  # A closed browser tab does not cancel the worker.
 def valid_host(self):return self.headers.get('Host','') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
 def do_GET(self):
  if not self.valid_host():return self.send({'error':'Use localhost to access FloorHAWK'},403)
  try:
   path=urlparse(self.path).path;app=self.server.app
   if path=='/api/config':return self.send({'token':app.token,'device':app.detector.device,'profile':app.profile,'profiles':app.profiles,'samples':[{'id':r['id'],'credit':r['credit']} for r in app.samples]})
   if path=='/api/evaluation':
    report=RESULTS_ROOT/'v1-gallery.json';return self.send(json.loads(report.read_text()) if report.exists() else {'reports':[],'note':'Offline evaluation has not been generated.'})
   if path.startswith('/gallery/'):
    # Only image paths registered in the offline gallery can be served; no arbitrary filesystem reads.
    gallery=json.loads((RESULTS_ROOT/'v1-gallery.json').read_text());key=path[len('/gallery/'):];allowed={s['overlay'] for report in gallery['reports'] for s in report['samples']}
    if key not in allowed:raise ValueError('Unknown gallery overlay')
    return self.send((ROOT/key).read_bytes(),mime='image/png')
   if path.startswith('/api/jobs/'):
    parts=path.split('/');ident=parts[3];job=app.get(ident);dest=STORE/ident;action=parts[4] if len(parts)>4 else ''
    if not action:return self.send(job)
    if action=='image':return self.send((dest/'image.png').read_bytes(),mime='image/png')
    if action=='export.json':
     if job['status']!='success':raise ValueError('No predictions to export')
     return self.send({'original_prediction':job['prediction'],'human_review':job['review'],'model_count':job['prediction']['predicted_count'],'reviewed_count':job['review']['reviewed_count'],'coordinate_system':'Original decoded image pixels; source EXIF orientation normalized before inference','credit':job['credit']},download='proofplan-review.json')
    if action=='export.png':
     if job['status']!='success':raise ValueError('No predictions to export')
     with app.guard:
      target=dest/f"review-{job['review']['revision']:04d}.png"
      if not target.exists():render(dest/'image.png',job['review']['boxes'],target,job['credit'],'Human review' if job['review']['reviewed'] else 'Unreviewed model predictions')
      return self.send(target.read_bytes(),mime='image/png',download='proofplan-reviewed.png')
    raise ValueError('Unknown action')
   static={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
   if path not in static:return self.send({'error':'Not found'},404)
   file=STATIC/static[path];return self.send(file.read_bytes(),mime=mimetypes.guess_type(str(file))[0] or 'text/plain')
  except (ValueError,KeyError,FileNotFoundError) as exc:self.send({'error':str(exc)},400)
 def do_POST(self):
  app=self.server.app
  if not self.valid_host() or self.headers.get('X-ProofPlan-Token')!=app.token:return self.send({'error':'Reload the local app before submitting.'},403)
  origin=self.headers.get('Origin')
  if origin and origin not in (f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}'):return self.send({'error':'Cross-origin requests are disabled'},403)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<=0 or length>29*1024*1024:raise ValueError('Request exceeds the image upload limit (20 MB file).')
   body=json.loads(self.rfile.read(length));path=urlparse(self.path).path
   if not isinstance(body,dict):raise ValueError('Expected JSON object')
   if path=='/api/jobs':
    if set(body)-{'image_base64','credit','sample','profile','task'}:raise ValueError('Unsupported upload field')
    return self.send(app.create(body),202)
   parts=path.split('/')
   if len(parts)==5 and parts[1:3]==['api','jobs'] and parts[4]=='review':return self.send(app.review(parts[3],body))
   self.send({'error':'Not found'},404)
  except (ValueError,KeyError,TypeError) as exc:self.send({'error':str(exc)},400)

def main():
 p=argparse.ArgumentParser();p.add_argument('--device',choices=['cpu','0'],default='cpu');p.add_argument('--port',type=int,default=8765);p.add_argument('--profile',choices=['baseline','hires','tiled']);a=p.parse_args()
 selected=ROOT/'selected-profile.json';profile=a.profile or (json.loads(selected.read_text())['profile'] if selected.exists() else 'baseline')
 server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.app=Application(a.device,profile)
 print(f'FloorHAWK: http://127.0.0.1:{a.port} | device={a.device} | profile={profile}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close();server.app.worker.shutdown(wait=True)
if __name__=='__main__':main()
