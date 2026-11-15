"""Answer-free paired scene review pilot/full source pass; shared durable budget."""
import json,hashlib,time,collections,argparse,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import v2.gemini as gemini
from .budget import CampaignLedger
from qa.common import sha
from runtime_paths import DATASET_ROOT
from .clock import atomic,admit,DEADLINES,now
from .review import request,VERSION
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def scan(folder,hashes):
 result={}
 for p in(ROOT/folder).glob('*.json'):
  try:r=json.loads(p.read_text())
  except ValueError:continue
  h=r.get('source_sha256')
  if h in hashes and h not in result and ('entities'in r or 'words'in r):result[h]=r
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=int,default=16);p.add_argument('--model',default='gemini-3.1-pro-preview');p.add_argument('--full',action='store_true');a=p.parse_args();gemini.Ledger=CampaignLedger
 manifest=json.loads((OUT/'observations/manifest.json').read_text())['sources'];hashes={r['source_sha256']for r in manifest};by=collections.defaultdict(list)
 # These are model outputs, never references. Sample IDs are removed from review payloads.
 for r in(json.loads(l)for l in(OUT/'candidate-local/predictions.jsonl').open()):
  if r.get('source_sha256')in hashes and r.get('question','').isascii():by[r['source_sha256']].append(r)
 custom={r['source_sha256']:json.loads((OUT/'observations/custom-yolo'/(r['key']+'.json')).read_text())for r in manifest};rtdetr=scan('cache/v2-rtdetr',hashes);rooms=scan('cache/v3-raster',hashes);ocr=scan('cache/v2-ocr',hashes)
 # Deterministic source-only selection, stratified by source drawing style, fixed before inference.
 styles=collections.defaultdict(list)
 for r in manifest:styles[Path(r['path']).stem.split('-')[0]].append(r)
 selected=[]
 for style,rs in sorted(styles.items()):
  rs.sort(key=lambda r:hashlib.sha256(('overnight-pilot-v1'+r['source_sha256']).encode()).hexdigest());selected+=rs[:max(1,a.pilot//len(styles))]
 selected=selected[:a.pilot]if not a.full else manifest
 selection=OUT/'review-selection.json'
 if not selection.exists():atomic(selection,{'version':VERSION,'sources':selected,'time':now(),'purpose':'Paired development diagnostic, source-only deterministic stratification; no expected answers supplied'})
 folder=OUT/'reviews'/a.model;folder.mkdir(parents=True,exist_ok=True);started=time.monotonic()
 def run(r):
  h=r['source_sha256'];dest=folder/(h+'.json')
  if dest.exists():return h,'cached'
  admit('optimize',65);observations=[('custom_yolo',custom[h])]+[('rtdetr',rtdetr[h])]if h in rtdetr else[('custom_yolo',custom[h])]
  if h in rooms:observations.append(('rooms',rooms[h]))
  locals_={}
  for local in by[h]:locals_.setdefault(local.get('task',{}).get('target'),local)
  try:
   result=request(DATASET_ROOT/r['path'],list(locals_.values()),observations,ocr.get(h,{}).get('words',[]),model=a.model)
   result.update(path=r['path'],observed_at=now(),status='success');atomic(dest,result);return h,'success'
  except Exception as exc:
   atomic(folder/(h+'.failure.json'),{'time':now(),'source_sha256':h,'status':'failed','error_type':type(exc).__name__,'reason':str(exc)[:160]});return h,type(exc).__name__
 with ThreadPoolExecutor(max_workers=2)as pool:
  futures=[pool.submit(run,r)for r in selected]
  for i,f in enumerate(as_completed(futures)):
   h,status=f.result();print(i+1,len(selected),h[:10],status,flush=True);atomic(folder/'progress.json',{'time':now(),'completed':i+1,'requested':len(selected),'seconds':time.monotonic()-started})
if __name__=='__main__':main()
