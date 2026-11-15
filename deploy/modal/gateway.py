"""Thin session/quotas gateway around the existing shared HTTP application."""
import os,json,time,threading,urllib.request,urllib.error,hashlib,hmac,secrets,base64,re
from pathlib import Path
from http.server import ThreadingHTTPServer
from deploy.modal.security import Controls,Denied
LOGIN='''<!doctype html><title>FloorHAWK · access</title><style>body{font:16px system-ui;max-width:500px;margin:15vh auto}input,button{font:inherit;padding:10px}</style><h1>FloorHAWK</h1><p>Private live drawing review. Enter your event access code.</p><form method="post" action="/access"><input name="code" type="password" autocomplete="off" required><button>Explore</button></form>'''

def issue_visitor_cookie(response,key):
 # Fresh random identity per browser; never a shared anonymous account.
 sid=secrets.token_hex(24);token=sid+'.'+hmac.new(key,sid.encode(),'sha256').hexdigest()
 response.set_cookie('floorhawk-session',token,httponly=True,secure=True,samesite='strict',max_age=8*3600)
 response.headers['Cache-Control']='private, no-store';response.headers['Vary']='Cookie'
 return response

def create_gateway(store,jobs_volume,dispatch,release):
 from fastapi import FastAPI,Request
 from fastapi.responses import Response,HTMLResponse,JSONResponse,RedirectResponse
 import qa_app,legacy_server
 import v2.budget
 snapshot=json.loads(Path('/opt/floorhawk/deploy/modal/budget-snapshot.json').read_text())
 class ReadOnlyLedger:
  def summary(self):return snapshot
 v2.budget.Ledger=ReadOnlyLedger
 import demo_gpu
 demo_gpu._enabled=True;demo_gpu.enabled=lambda:False
 class NoDispatch:
  def submit(self,*args,**kwargs):return None
  def shutdown(self,*args,**kwargs):return None
 class CloudApplication(qa_app.Application):
  def admission_busy(self):return False # Atomic external admission bounds the Modal queue.
  def get(self,ident):
   if not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Unknown job')
   path=qa_app.STORE/ident/'job.json'
   if not path.exists():raise ValueError('Unknown job')
   return json.loads(path.read_text())
 app=CloudApplication('cpu');app.samples=[];app.worker.shutdown(wait=False);app.worker=NoDispatch();app.pipeline.set_cloud(False);app.pipeline.local_routing=False
 from deploy.modal.publication import PublishedJobs
 published=PublishedJobs(jobs_volume)
 server=ThreadingHTTPServer(('127.0.0.1',0),qa_app.Handler);server.app=app;threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
 if os.environ.get('FLOORHAWK_PRESENTER')=='1':
  from deploy.modal.presenter_controls import PresenterControls
  controls_class=PresenterControls
 else:controls_class=Controls
 controls=controls_class(store,os.environ['FLOORHAWK_ACCESS_HASH']);key=os.environ['FLOORHAWK_SESSION_KEY'].encode();web=FastAPI(docs_url=None,redoc_url=None)
 def session(request):
  token=request.cookies.get('floorhawk-session','');parts=token.split('.')
  if len(parts)!=2 or not hmac.compare_digest(hmac.new(key,parts[0].encode(),'sha256').hexdigest(),parts[1]):return None
  return parts[0]
 def forward(path,method='GET',body=None):
  req=urllib.request.Request(origin+path,data=body,method=method,headers={'Content-Type':'application/json','X-ProofPlan-Token':app.token})
  try:r=urllib.request.urlopen(req,timeout=60)
  except urllib.error.HTTPError as e:r=e
  return Response(r.read(),status_code=r.status,headers={k:v for k,v in r.headers.items()if k.lower()in ['content-type','content-disposition','cache-control','content-security-policy','x-content-type-options']})
 @web.get('/health')
 def health():return {'ready':True,'application':'FloorHAWK','api_contract':'floorhawk.jobs.v1','release':release,'live':controls.allowance()['live'],'gemini':controls.allowance()['gemini']}
 @web.post('/access')
 async def access(request:Request):
  from urllib.parse import parse_qs
  raw=await request.body()
  if len(raw)>2048:return JSONResponse({'error':'Invalid code'},403)
  code=parse_qs(raw.decode()).get('code',[''])[0]
  if not controls.authenticate(code):return JSONResponse({'error':'Invalid access code'},403)
  return issue_visitor_cookie(RedirectResponse('/',status_code=303),key)
 @web.api_route('/{path:path}',methods=['GET','POST'])
 async def proxy(path:str,request:Request):
  sid=session(request)
  if not sid:
   # Only the server-selected public role bootstraps anonymous sessions.
   if os.environ.get('FLOORHAWK_EVENT_ROLE')=='public' and request.method=='GET'and path=='':
    return issue_visitor_cookie(forward('/'),key)
   return HTMLResponse(LOGIN)if request.method=='GET'and path==''else JSONResponse({'error':'Visitor session required'if os.environ.get('FLOORHAWK_EVENT_ROLE')=='public'else'Event access code required'},401)
  route='/'+path+('?' +request.url.query if request.url.query else'')
  try:
   if path.startswith('api/submissions/'):
    submission_key=path.rsplit('/',1)[1];st=store.get('admission-state-v1',{});item=st.get('idempotency',{}).get(sid+':'+submission_key);ident=item.get('id')if item else None;row=st.get('jobs',{}).get(ident,{})
    return JSONResponse({'id':ident if row.get('status')not in [None,'reserved']else None})
   if path=='api/gallery':
    from deploy.modal.gallery import catalog
    return JSONResponse(catalog())
   if path=='api/validate'and request.method=='POST':
    from deploy.modal.display_assets import validate
    raw=await request.body()
    if len(raw)>28*1024**2:raise ValueError('Upload exceeds28MiB')
    return JSONResponse(validate(json.loads(raw)))
   if path.startswith('api/gallery/'):
    from deploy.modal.gallery import drawing
    row,source=drawing(path.split('/')[2]);return Response(source.read_bytes(),media_type={'PNG':'image/png','PDF':'application/pdf','IFC':'application/octet-stream'}[row['format']])
   if path.startswith('api/jobs/'):
    ident=path.split('/')[2];row=controls.own(sid,ident);published.sync(ident,app.get)
    if (path.endswith('/model')or path.endswith('/model.glb'))and request.method=='GET':
     j=app.get(ident)
     source_hash=j.get('source_sha256','')
     if (os.environ.get('FLOORHAWK_PRESENTER')=='1'or os.environ.get('FLOORHAWK_EVENT_ROLE')in['public','judges','presenter','candidate'])and j.get('input_kind')=='ifc'and re.fullmatch('[a-f0-9]{64}',source_hash):
      folder=Path('/weights/presenter-geometry')/source_hash
      if (folder/'metadata.json').is_file():
       metadata=json.loads((folder/'metadata.json').read_text())
       if metadata.get('source_sha256')!=source_hash:raise ValueError('Geometry source mismatch')
       if path.endswith('/model.glb'):
        raw=(folder/'model.glb').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=metadata['glb_sha256']:raise ValueError('Geometry checksum mismatch')
        return Response(raw,media_type='model/gltf-binary')
       metadata['glb_url']=f'/api/jobs/{ident}/model.glb';return JSONResponse(metadata)
     return JSONResponse({'status':'unavailable','note':'No verified cached geometry; properties remain available'})
    if request.method=='POST':raise Denied('Cloud review mutation is disabled for this deployment',0)
    if path.endswith('/annotated.png'):
     from deploy.modal.display_assets import annotated
     from urllib.parse import parse_qs
     return Response(annotated(app,app.get(ident),int(parse_qs(request.url.query).get('page',['1'])[0])),media_type='image/png',headers={'Content-Disposition':'attachment; filename=floorhawk-annotated.png'})
    result=forward(route)
    if path.count('/')==2 and result.status_code==200:
     j=json.loads(result.body)
     from deploy.modal.gallery import reference
     j['expected_reference']=reference(row.get('gallery_id'),j.get('question',''));result=JSONResponse(j)
     if row.get('status')=='execution_error'and j['status']in ['queued','running']:
      j.update(status='failed',stage='Interrupted cloud worker',error=row.get('recovery_reason','Worker interrupted; retry as a new request'));result=JSONResponse(j)
     if j['status']not in ['queued','running']and row.get('status')!=j['status']:controls.complete(ident,j['status'])
    return result
   if path=='api/allowance':return controls.allowance()
   if path=='api/budget'and os.environ.get('FLOORHAWK_EVENT_ROLE'):
    from deploy.modal.presenter_budget import PresenterLedger
    return JSONResponse(PresenterLedger().summary())
   if path in ['api/config','api/budget']:
    result=forward(route);data=json.loads(result.body)
    if path=='api/config':data.update(samples=[],host_vision=True,release=release,api_contract='floorhawk.jobs.v1');data['cloud']={'enabled':True,'default_mode':'hybrid'};data['unified_hybrid']=True;data['presenter']=os.environ.get('FLOORHAWK_PRESENTER')=='1'
    return JSONResponse(data)
   if path=='api/cloud-state':return JSONResponse({'enabled':False,'note':'Gemini disabled: shared lifetime accounting not connected'})
   if path=='api/jobs'and request.method=='POST':
    if int(request.headers.get('content-length','0'))>28*1024**2:raise Denied('Upload request exceeds28MiB bound',0)
    raw=await request.body()
    if len(raw)>28*1024**2:raise Denied('Upload request exceeds28MiB bound',0)
    data=json.loads(raw);gallery_id=data.pop('gallery_id',None);reuse=data.pop('reuse_job_id',None)
    if reuse:
     owner=controls.own(sid,reuse);jobs_volume.reload();old=app.get(reuse);source=qa_app.STORE/reuse/old['source_file'];data.update(file_name=old['source_name'],file_base64=base64.b64encode(source.read_bytes()).decode(),credit=old.get('credit',''));gallery_id=owner.get('gallery_id')
    if gallery_id:
     from deploy.modal.gallery import drawing
     row,source=drawing(gallery_id);data.update(file_name=row['filename'],file_base64=base64.b64encode(source.read_bytes()).decode(),credit=row['credit'])
    data['mode']='hybrid';raw=json.dumps(data).encode();mode='hybrid';payload=base64.b64decode(data.get('file_base64',''),validate=True)
    if len(payload)>20*1024**2:raise Denied('Source exceeds20MiB bound',0)
    suffix=Path(data.get('file_name','')).suffix.lower()
    if suffix=='.pdf':
     import pymupdf
     with pymupdf.open(stream=payload,filetype='pdf')as d:
      if len(d)>20:raise Denied('Cloud PDF limit is20pages',0)
    if suffix=='.ifc'and (len(payload)>10*1024**2 or payload.count(b'=IFC')>100000):raise Denied('IFC exceeds10MiB/100k STEP entity bound',0)
    # Same body within five seconds is a double-click/retry, not a second accepted job.
    idem=request.headers.get('Idempotency-Key')or 'auto:'+hashlib.sha256(raw).hexdigest();review_enabled=bool(controls.allowance().get('gemini'));admission_mode='local'if os.environ.get('FLOORHAWK_EVENT_ROLE')and not review_enabled else mode
    reservation,new=controls.reserve(sid,idem,False if gallery_id else hashlib.sha256(payload).hexdigest(),release,admission_mode)
    if not new:return JSONResponse({'id':reservation},202)
    try:
     result=forward('/api/jobs','POST',raw)
     if result.status_code>=400:controls.rollback(reservation);return result
     ident=json.loads(result.body)['id']
     from qa.common import write_json
     job=app.get(ident);job['submission_release']=release;job['api_contract']='floorhawk.jobs.v1';job['gemini_enabled_at_submission']=review_enabled;write_json(qa_app.STORE/ident/'job.json',job)
     controls.publish(reservation,ident,metadata={'gallery_id':gallery_id}if gallery_id else {})
     reservation=ident;jobs_volume.commit();dispatch(ident);return result
    except Exception:controls.rollback(reservation);raise
   if request.method=='GET'and(path in ['', 'app.js','style.css','ifc-viewer.js']or path.startswith('vendor/')):return forward(route)
   return JSONResponse({'error':'Not found'},404)
  except Denied as e:return JSONResponse({'error':str(e),'allowance':controls.allowance(),'retry_seconds':e.retry},429 if e.retry else 404,headers={'Retry-After':str(e.retry)})
  except (ValueError,TypeError)as e:return JSONResponse({'error':str(e)},400)
  except Exception as e:return JSONResponse({'error':'Server request failed ('+type(e).__name__+'). Reconnect to an accepted job before retrying submission.'},500)
 return web
