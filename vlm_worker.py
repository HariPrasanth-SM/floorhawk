from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""One local Qwen3-VL-2B worker; explicit CUDA health/blocking; never executes generated code."""
import argparse,base64,io,json,threading,time,traceback
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from qa.common import ROOT,inference_lock,write_json
from qa.router import validate_task
QWEN_REV='89644892e4d85e24eaac8bacfd4f463576704203'
class Worker:
 def __init__(self,device):
  import torch
  from transformers import Qwen3VLForConditionalGeneration,AutoProcessor
  self.device=device;self.model=None;self.processor=None;self.busy=threading.Lock();self.error=None;self.torch=torch
  self.weights=MODEL_ROOT/'qwen3-vl-2b'
  if device=='cuda:0' and not torch.cuda.is_available():self.error='CUDA unavailable in this process. Run this worker in the normal GPU-enabled Ubuntu terminal.'
  elif not (self.weights/'model.safetensors').exists():self.error='Weights missing: run .venv/bin/python assets.py qwen'
  self.runtime={'transformers':__import__('transformers').__version__,'torch':torch.__version__,'cuda':torch.version.cuda}
 def unload(self):
  # Release instead of copying GPU weights back to RAM; reload only on next admission.
  import gc
  self.model=None;self.processor=None;gc.collect()
  if self.device.startswith('cuda'):self.torch.cuda.empty_cache()
 def health(self):return {'ready':self.error is None,'status':'blocked' if self.error else ('busy' if self.busy.locked() else 'available'),'error':self.error,'model':'Qwen/Qwen3-VL-2B-Instruct','revision':QWEN_REV,'device':self.device,'loaded':self.model is not None,'runtime':self.runtime,'peak_gpu_memory_bytes':getattr(self,'peak',None),'cloud_enabled':False}
 def answer(self,body):
  if self.error:return {'status':'failed','error':self.error,'warnings':[self.error]}
  if not self.busy.acquire(blocking=False):return {'status':'failed','error':'Worker busy; retry after current local generation.'}
  try:
   with inference_lock():
    from transformers import Qwen3VLForConditionalGeneration,AutoProcessor
    from PIL import Image
    routing=body.get('mode')=='route';inventory=body.get('mode')=='inventory';task=None if routing or inventory else validate_task(body['task']);question=body.get('question','Extract a conservative visual inventory')
    if not isinstance(question,str) or len(question)>4000:raise ValueError('Invalid question')
    image=None
    if not routing:
     image=Image.open(io.BytesIO(base64.b64decode(body['image_base64'],validate=True))).convert('RGB');image.thumbnail((768,768))
    started=time.perf_counter();t=started
    provenance=json.loads((self.weights/'provenance.json').read_text())
    if self.model is None:
     from assets import sha
     for name,h in provenance['files'].items():
      if sha(self.weights/name)!=h:raise RuntimeError('Local model checksum mismatch: '+name)
     self.processor=AutoProcessor.from_pretrained(self.weights,local_files_only=True,min_pixels=65536,max_pixels=262144)
     self.model=Qwen3VLForConditionalGeneration.from_pretrained(self.weights,local_files_only=True,torch_dtype=self.torch.bfloat16 if self.device.startswith('cuda') else self.torch.float32,attn_implementation='sdpa',device_map=self.device if self.device.startswith('cuda') else None,low_cpu_mem_usage=True)
     self.model.eval()
    self.model.to(self.device);load=time.perf_counter()-t
    prompt='Answer the question from this image. Return ONLY JSON {"answer": number or string, "unit": "count"/"m2"/"m3"/"m"/null, "status":"success" or "abstained", "warning":string}. If uncertain or missing evidence, abstain. Do not claim boxes or calibrated confidence. Task: '+json.dumps(task)+'\nQuestion: '+question+'\nExtracted evidence: '+json.dumps(body.get('evidence',[]),ensure_ascii=False)[:6000]
    if inventory:
     prompt='Inspect this floor plan and return ONLY JSON with counts (object) and warnings (string). Keys in counts: window, door, toilet_fixture, sink, shower_bath, sauna, bedroom, kitchen, bathroom, wc_room, balcony, apartment, storey, room. Values must be nonnegative integers or null when not confidently supported. A double sink is one fixture, WC room is not a toilet bowl, shower_bath is the combined number of showers and bathtubs. No physical area estimates. Do not imply completeness. Extracted entities: '+json.dumps(body.get('evidence',[]),ensure_ascii=False)[:5000]
    if routing:
     from qa.router import OPERATIONS,TARGETS
     prompt='Map this question to a registered task. Return ONLY JSON with operation, target, filters (object), scope (drawing/model/floor), requested_unit (count/m2/m3/m/null), required_evidence (list). Operations: '+str(sorted(OPERATIONS))+' Targets: '+str(sorted(TARGETS))+' Question: '+question
    messages=[{'role':'user','content':([{'type':'image','image':image}] if image is not None else [])+[{'type':'text','text':prompt}]}]
    inputs=self.processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt').to(self.device)
    if self.device.startswith('cuda'):self.torch.cuda.reset_peak_memory_stats();self.torch.cuda.synchronize()
    t=time.perf_counter()
    with self.torch.inference_mode():output=self.model.generate(**inputs,max_new_tokens=384 if inventory else 192,do_sample=False)
    if self.device.startswith('cuda'):self.torch.cuda.synchronize();self.peak=self.torch.cuda.max_memory_allocated()
    text=self.processor.batch_decode(output[:,inputs['input_ids'].shape[1]:],skip_special_tokens=True)[0];begin=text.find('{');end=text.rfind('}')+1
    parsed=json.loads(text[begin:end]);status=parsed.get('status')
    if inventory:
     from qa.router import TARGETS
     counts=parsed.get('counts',{})
     if not isinstance(counts,dict) or any(k not in TARGETS or (v is not None and (isinstance(v,bool) or not isinstance(v,int) or v<0)) for k,v in counts.items()):raise ValueError('Invalid inventory counts')
     result={'status':'success' if any(v is not None for v in counts.values()) else 'abstained','counts':counts,'evidence':[],'warnings':[str(parsed.get('warnings',''))],'model':{'repository':provenance['repository'],'revision':QWEN_REV,'weights_sha256':provenance['files']['model.safetensors'],'license':'Apache-2.0'},'timing':{'model_loading_seconds':load,'inference_seconds':time.perf_counter()-t,'total_seconds':time.perf_counter()-started},'peak_gpu_memory_bytes':getattr(self,'peak',None)}
     self.unload()
     if self.device.startswith('cuda'):self.torch.cuda.empty_cache()
     return result
    if routing:
     routed=validate_task(parsed);routed['router']='local Qwen3-VL text-only registered-task interpretation'
     self.unload()
     if self.device.startswith('cuda'):self.torch.cuda.empty_cache()
     return {'status':'success','task':routed,'revision':QWEN_REV,'peak_gpu_memory_bytes':getattr(self,'peak',None)}
    if status not in ('success','abstained'):raise ValueError('Invalid generated status')
    if status=='success' and not isinstance(parsed.get('answer'),(str,int,float)):raise ValueError('Invalid typed answer')
    if parsed.get('unit') not in ('count','m2','m3','m',None):raise ValueError('Invalid generated unit')
    result={'status':status,'answer':parsed.get('answer') if status=='success' else None,'unit':parsed.get('unit'),'evidence':[],'warnings':[str(parsed.get('warning',''))],'model':{'repository':provenance['repository'],'revision':QWEN_REV,'weights_sha256':provenance['files']['model.safetensors'],'license':'Apache-2.0','training_overlap':'unknown'},'calculation_trace':[{'operation':'direct_visual_estimate','grounded':False}],'timing':{'model_loading_seconds':load,'inference_seconds':time.perf_counter()-t,'total_seconds':time.perf_counter()-started},'peak_gpu_memory_bytes':getattr(self,'peak',None)}
    self.unload()
    if self.device.startswith('cuda'):self.torch.cuda.empty_cache()
    return result
  except Exception as e:
   if self.model is not None:self.unload()
   return {'status':'failed','answer':None,'unit':None,'evidence':[],'warnings':[str(e)],'error':str(e),'traceback':traceback.format_exc()}
  finally:self.busy.release()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):pass
 def send(self,data,status=200):
  data=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except BrokenPipeError:pass
 def do_GET(self):self.send(self.server.worker.health() if self.path=='/health' else {'error':'not found'},200 if self.path=='/health' else 404)
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin:return self.send({'error':'Browser-origin requests are not accepted by the internal worker'},403)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if self.path!='/answer' or length<=0 or length>8*1024**2:raise ValueError('Invalid worker request')
   self.send(self.server.worker.answer(json.loads(self.rfile.read(length))))
  except Exception as e:self.send({'status':'failed','error':str(e)},400)
def main():
 p=argparse.ArgumentParser();p.add_argument('--device',choices=['cuda:0','cpu'],default='cuda:0');p.add_argument('--port',type=int,default=8766);a=p.parse_args();w=Worker(a.device);server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.worker=w
 write_json(RESULTS_ROOT/'vlm-health.json',w.health());print(json.dumps(w.health()),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
