import os
"""Read-only replay server. Standard library only: no models/providers/inference.
No external network clients, no POST execution endpoints; localhost serving only.
"""
import argparse,json,mimetypes,time,hashlib,re
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,data,status=200,mime='application/json'):
  b=data if isinstance(data,bytes) else json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(b)));self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(b)
 def do_POST(self):self.send({'error':'RECORDED REPLAY: live computation and edits disabled'},405)
 def do_GET(self):
  host=self.headers.get('Host','')
  if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):return self.send({'error':'Use localhost'},403)
  t=time.perf_counter();path=urlparse(self.path).path;state=self.server.state
  if path in ('/health','/api/config'):return self.send({'ready':True,'diagnostics':os.environ.get('PROOFPLAN_DIAGNOSTICS')=='1','replay':True,'device':'recorded','token':'','vlm':{'ready':False,'status':'not used in replay'},'samples':[{'id':r['sample_id'],'credit':r['question'],'modes':r['modes']} for r in state['records']],'banner':state['banner'],'coverage_gaps':state['coverage_gaps'],'cloud':{'enabled':False}})
  if path=='/api/qa-evaluation':return self.send({'reports':[],'note':'References appear below recorded answers; no live evaluation runs.'})
  if path in ('/','/index.html','/app.js','/style.css'):
   name='index.html' if path=='/' else path.lstrip('/');return self.send((ROOT/'web'/name).read_bytes(),mime=mimetypes.guess_type(name)[0] or 'text/plain')
  parts=path.strip('/').split('/')
  if len(parts)>=3 and parts[:2]==['api','jobs']:
   ident=parts[2]
   if ident not in self.server.ids:return self.send({'error':'not recorded'},404)
   dest=self.server.bundle/ident;job=json.loads((dest/'job.json').read_text());action=parts[3] if len(parts)>3 else ''
   if not action:job['replay']['retrieval_seconds']=time.perf_counter()-t;return self.send(job)
   if action=='export.json':return self.send({'original_prediction':job['prediction'],'human_review':job['review'],'replay':job['replay'],'credit':job['credit']})
   page=int(parts[4]) if action=='page' and len(parts)==5 else int(parse_qs(urlparse(self.path).query).get('page',['1'])[0]);f=dest/(f'annotated-{page}.png' if action=='export.png' else f'page-{page}.png')
   if action in ('image','page','export.png') and f.exists():return self.send(f.read_bytes(),mime='image/png')
  return self.send({'error':'not recorded'},404)
def main():
 import socket
 def denied_egress(*args,**kwargs):raise RuntimeError('Replay prohibits outbound network connections')
 socket.socket.connect=denied_egress
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--port',type=int,default=8765);p.add_argument('--include-failures',action='store_true');a=p.parse_args();
 for name,expected in json.loads((a.bundle/'checksums.json').read_text()).items():
  f=a.bundle/name
  if f.is_symlink() or not f.resolve().is_relative_to(a.bundle.resolve()) or not f.is_file():raise ValueError('Unsafe or missing replay member')
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
  if h.hexdigest()!=expected:raise ValueError('Replay checksum mismatch: restore sealed bundle')
 index=json.loads((a.bundle/'index.json').read_text());allrecords=index['records'];index['records']=[r for r in allrecords if a.include_failures or any(m['correct'] for m in r['modes'].values())][:20 if not a.include_failures else len(allrecords)];allcategories={r['category'] for r in allrecords};covered={r['category'] for r in index['records']};index['coverage_gaps']=sorted(str(k) for k in allcategories-covered);
 if not a.include_failures:
  for r in index['records']:r['modes']={k:m for k,m in r['modes'].items() if m['correct']}
 s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);s.bundle=a.bundle;s.state=index;s.ids={m['id'] for r in index['records'] for m in r['modes'].values()};
 if any(not re.fullmatch(r'[A-Za-z0-9_-]+',ident) for ident in s.ids):raise ValueError('Unsafe replay identifier')
 print(index['banner']+' http://127.0.0.1:'+str(a.port),flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
if __name__=='__main__':main()
