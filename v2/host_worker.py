"""Authenticated localhost configured-model worker with host telemetry and one queue."""
import argparse,base64,hmac,json,os,secrets,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from .policy import ROOT,STATE
from .supervisor import sample,Admission
from qa.common import write_json
TOKEN=STATE/'host-worker.token'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,data,status=200):
  b=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers()
  try:self.wfile.write(b)
  except BrokenPipeError:pass
 def authorized(self):return not self.headers.get('Origin') and hmac.compare_digest(self.headers.get('X-FloorHAWK-Worker',''),self.server.token)
 def do_GET(self):
  if not self.authorized():return self.send({'error':'worker authentication required'},403)
  if self.path=='/health':return self.send({'worker':self.server.worker.health(),'telemetry':self.server.telemetry,'scope':os.environ.get('PROOFPLAN_SCOPE','monitor-only'),'vision':True})
  return self.send({'error':'not found'},404)
 def do_POST(self):
  if not self.authorized():return self.send({'error':'worker authentication required'},403)
  n=int(self.headers.get('Content-Length',0))
  if self.path!='/answer' or not 0<n<=8*1024**2:return self.send({'error':'invalid request'},400)
  decision=self.server.admission.check(self.server.telemetry,True)
  if decision!='admit':return self.send({'status':'blocked','error':'Resource admission: '+decision},503)
  if not self.server.queue.acquire(False):return self.send({'status':'blocked','error':'GPU queue busy'},409)
  try:
   body=json.loads(self.rfile.read(n))
   if set(body)-{'mode','image_base64','task','question','evidence','model','settings'}:raise ValueError('Unknown worker field')
   if body.get('mode') not in ('route','inventory','answer','vision'):raise ValueError('Unknown worker operation')
   if body.get('mode')=='vision':
    from demo_gpu import host_vision
    self.server.worker.unload()
    self.send(host_vision(body))
   else:
    from demo_gpu import release_host_models
    release_host_models()
    self.send(self.server.worker.answer(body))
  except Exception:self.send({'status':'failed','error':'Worker request failed; no arbitrary execution permitted'},400)
  finally:self.server.queue.release()

def monitor(server):
 with (STATE/'host-resources.jsonl').open('a') as f:
  while not server.stopping.is_set():
   s=sample(os.getpid(),gpu=True);server.telemetry=s;write_json(STATE/'host-telemetry.json',s);f.write(json.dumps(s)+'\n');f.flush()
   decision=server.admission.check(s,True)
   if decision in ('shed','telemetry-unavailable','disk-pressure') and server.queue.locked():
    write_json(STATE/'host-pressure-stop.json',{'decision':decision,'time':time.time(),'resumable':True});os._exit(78)
   server.stopping.wait(1)

def main():
 os.environ['PROOFPLAN_IN_HOST']='1'
 import torch
 torch.set_num_threads(2);torch.set_num_interop_threads(2)
 from vlm_worker import Worker
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);a=p.parse_args()
 fd=os.open(TOKEN,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);token=secrets.token_urlsafe(32)
 with os.fdopen(fd,'w') as f:f.write(token)
 s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);s.token=token;s.worker=Worker('cuda:0');s.queue=threading.Lock();s.admission=Admission();s.telemetry=sample(os.getpid(),True);s.stopping=threading.Event();threading.Thread(target=monitor,args=(s,),daemon=True).start()
 write_json(STATE/'host-worker-status.json',{'pid':os.getpid(),'port':a.port,'cuda':torch.cuda.is_available(),'token_path':str(TOKEN),'scope':os.environ.get('PROOFPLAN_SCOPE','monitor-only'),'vision':True})
 print('FloorHAWK host worker: localhost:'+str(a.port)+'; token stored privately; no model loaded until admitted request.',flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.stopping.set();s.server_close()
if __name__=='__main__':main()
