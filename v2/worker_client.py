"""Private token stays server-side; only fixed authenticated worker operations."""
import base64,json,urllib.request,time
from runtime_paths import WORKER_URL
from pathlib import Path
from .policy import STATE

def request(body=None,timeout=180):
 if body is not None:
  from .supervisor import fresh_host
  telemetry=fresh_host();required_mib=4500
  if body.get('mode')=='vision':required_mib=2000 if body.get('model')=='custom_yolo'else 1400 if body.get('model')=='rtdetr' else 2200 if body.get('settings',{}).get('max_edge')==1024 else 1200
  target_mib=telemetry.get('gpu_total_mib',0)*.65
  if not telemetry.get('gpu_available') or target_mib-telemetry.get('gpu_used_mib',0)<required_mib:
   raise RuntimeError(f'Model admission blocked:{required_mib}MiB incremental budget would exceed65% total VRAM including other processes. CPU/local fallback retained.')
 token=(STATE/'host-worker.token').read_text().strip();headers={'X-FloorHAWK-Worker':token,'Content-Type':'application/json'}
 req=urllib.request.Request(WORKER_URL+('/health' if body is None else '/answer'),data=None if body is None else json.dumps(body).encode(),headers=headers)
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def smoke():
 from .policy import ROOT
 from qa.common import write_json
 image=ROOT.parent/'datasets/junction-dataset/data/cubicasa5k/colorful-12094.png'
 from PIL import Image
 import io
 im=Image.open(image).convert('RGB');im.thumbnail((768,768));b=io.BytesIO();im.save(b,format='PNG')
 t=time.perf_counter();result=request({'mode':'inventory','image_base64':base64.b64encode(b.getvalue()).decode(),'question':'Extract a conservative inventory','evidence':[]},240)
 result.update(preflight_image=str(image.relative_to(ROOT.parent)),wall_seconds=time.perf_counter()-t);write_json(STATE/'host-real-inference.json',result);print(json.dumps(result))
if __name__=='__main__':smoke()
