import os
from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Paginated saved-result replay, source rendering and precomputed IFC context.
Never imports inference pipelines/providers; never transmits references to live routes.
"""
import argparse,json,mimetypes,time,urllib.parse,hashlib,sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from qa.common import ROOT
from .store import Store,DB
from . import assets
from .ifc_geometry import CACHE,key
STATIC={'index.html','app.js','style.css','ifc-viewer.js'}
VENDOR={'three.module.js','OrbitControls.js','GLTFLoader.js','BufferGeometryUtils.js','LICENSE.three'}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,data,status=200,mime='application/json',download=None):
  raw=data if isinstance(data,bytes)else json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
  if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
  self.end_headers()
  try:self.wfile.write(raw)
  except BrokenPipeError:pass
 def do_POST(self):return self.send({'error':'Recorded replay has no inference/edit endpoint'},405)
 def do_GET(self):
  if self.headers.get('Host')not in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']:return self.send({'error':'Use localhost'},403)
  u=urllib.parse.urlparse(self.path);path=u.path;params=urllib.parse.parse_qs(u.query);get=lambda k,d='':params.get(k,[d])[0];store=self.server.store
  try:
   if path in ['/health','/api/config']:
    runs=store.runs();return self.send({'ready':True,'diagnostics':os.environ.get('PROOFPLAN_DIAGNOSTICS')=='1','inference_modules_loaded':[n for n in ['torch','ultralytics','google.genai','qa.pipeline','v3.pipeline']if n in sys.modules],'replay':True,'inspection':True,'device':'recorded','token':'','samples':[],'runs':[{'id':r['id'],'label':r.get('label',r['id']),'available_modes':r.get('available_modes',[r['mode']]),'mode':r['mode'],'manifest_n':r['manifest_n'],'recorded':r['recorded'],'source_sha256':r['sha256']}for r in runs],'default_run':'v3-release-quick','default_outcome':self.server.default_outcome,'coverage_gaps':[],'banner':'Recorded replay — no live inference','vlm':{'ready':False,'status':'not used'},'cloud':{'enabled':False}})
   if path=='/api/inspection/facets':return self.send(store.facets(get('run','v3-release-quick')))
   if path=='/api/inspection/cases':return self.send(store.cases(get('run','v3-release-quick'),get('mode','local'),get('outcome','all'),get('format'),get('dataset'),get('target'),int(get('page','0'))))
   if path=='/api/inspection/curated':return self.send(store.curated(get('run','v3-release-quick'),get('mode','local')))
   if path in ['/analytics/report','/analytics/summary.json','/analytics/rows.csv','/analytics/rows.jsonl']:
    name=path.rsplit('/',1)[-1];file=ROOT/'SOLUTION_ANALYTICS.md'if name=='report'else (RESULTS_ROOT/'iteration60'/({'summary.json':'current-summary.json','rows.csv':'current-rows.csv','rows.jsonl':'current-rows.jsonl'}[name]) if (RESULTS_ROOT/'iteration60/current-summary.json').exists() else RESULTS_ROOT/'inspection'/({'summary.json':'summary.json','rows.csv':'quick-rows.csv','rows.jsonl':'quick-rows.jsonl'}[name]));return self.send(file.read_bytes(),mime='text/markdown; charset=utf-8'if name=='report'else'application/json'if name.endswith('.json')else'text/csv; charset=utf-8'if name.endswith('.csv')else'application/x-ndjson',download=file.name)
   if path=='/api/qa-evaluation':return self.send({'reports':[],'note':'Full saved-result analytics: SOLUTION_ANALYTICS.md; reference shown only in recorded inspection.'})
   if path in ['/','/index.html','/app.js','/style.css','/ifc-viewer.js']or path.startswith('/vendor/'):
    name=path.lstrip('/')or'index.html'
    if name not in STATIC and not(name.startswith('vendor/')and name[7:]in VENDOR):raise ValueError('Unknown viewer asset')
    return self.send((ROOT/'web'/name).read_bytes(),mime=mimetypes.guess_type(name)[0]or'text/plain')
   parts=path.strip('/').split('/')
   if len(parts)>=3 and parts[:2]==['api','jobs']:
    ident=parts[2];job=store.job(ident);source=store.source(ident);action=parts[3]if len(parts)>3 else''
    if not action:job['replay']['retrieval_seconds']=0;return self.send(job)
    if action=='export.json':return self.send({'original_prediction':job['prediction'],'human_review':job['review'],'replay':job['replay'],'credit':job['credit']},download='proofplan-saved-result.json')
    if action in ['model','model.glb']:
     if source.suffix.lower()!='.ifc':raise ValueError('Not an IFC case')
     folder=CACHE/key(source);meta=folder/'metadata.json'
     if not meta.exists():return self.send({'status':'not_precomputed','note':'No cached geometry. Saved answer/IFC properties remain available.'})
     if action=='model.glb':return self.send((folder/'model.glb').read_bytes(),mime='model/gltf-binary')
     data=json.loads(meta.read_text());data['glb_url']=f'/api/jobs/{ident}/model.glb';return self.send(data)
    pn=int(parts[4])if action=='page'and len(parts)>4 else int(get('page','1'))
    if not 1<=pn<=len(job['pages']):raise ValueError('Unknown page')
    if action in ['crop.png','crop.json']:
     box=[float(x)for x in get('bbox').split(',')];file,info=assets.crop(source,pn,box,job['pages'][pn-1]);return self.send(info if action=='crop.json'else file.read_bytes(),mime='application/json'if action=='crop.json'else'image/png')
    if action in ['image','page','export.png']:
     file,_=assets.preview(source,pn)
     if action=='export.png':
      from detector import render
      out=assets.CACHE/('annotated-'+hashlib.sha256((ident+json.dumps(job['review']['boxes'],sort_keys=True)).encode()).hexdigest()+'-'+str(pn)+'.png')
      if not out.exists():render(file,[b for b in job['review']['boxes']if b['page']==pn],out,job['credit'],'Recorded prediction; reference is separate and has no invented geometry')
      assets.budget_cache(out)
      return self.send(out.read_bytes(),mime='image/png',download='proofplan-recorded-evidence.png')
     return self.send(file.read_bytes(),mime='image/png')
   return self.send({'error':'Unknown recorded inspection endpoint'},404)
  except (ValueError,KeyError,FileNotFoundError,IndexError,TypeError)as e:return self.send({'error':str(e)},400)
 def handle_error(self):pass

def main():
 import socket
 def no_outbound(*a,**kw):raise RuntimeError('Replay forbids outbound connections')
 socket.socket.connect=no_outbound
 p=argparse.ArgumentParser();p.add_argument('--index',type=Path,default=DB);p.add_argument('--port',type=int,default=8767);p.add_argument('--include-failures',action='store_true');a=p.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.store=Store(a.index);server.default_outcome='all'if a.include_failures else'correct';print('Recorded replay — no live inference http://127.0.0.1:'+str(a.port),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
