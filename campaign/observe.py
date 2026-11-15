"""Answer-free, resumable custom-model source observations. No reference imports."""
import json,base64,time,hashlib,os
from pathlib import Path
import modal
from runtime_paths import DATASET_ROOT
from qa.common import sha
from .clock import admit,DEADLINES,atomic,now
from .extraction import SHA,SETTINGS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115';CACHE=OUT/'observations/custom-yolo';CACHE.mkdir(parents=True,exist_ok=True)
def key(source):return hashlib.sha256(json.dumps([source,SHA,SETTINGS],sort_keys=True).encode()).hexdigest()
def main():
 rows=[json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.questions.jsonl').open()];paths=sorted({r['path']for r in rows if Path(r['path']).suffix.lower()in['.png','.jpg','.jpeg']});items=[]
 for path in paths:
  file=(DATASET_ROOT/path).resolve();assert file.is_relative_to(DATASET_ROOT);h=sha(file);items.append({'path':path,'source_sha256':h,'key':key(h)})
 atomic(OUT/'observations/manifest.json',{'question_manifest_sha256':sha(ROOT/'benchmarks/qa-v3/quick.questions.jsonl'),'settings':SETTINGS,'weight_sha256':SHA,'sources':items,'references_available_to_runner':False});worker=modal.Cls.from_name('floorhawk-campaign-extraction','Extractor')();done=0;start=time.monotonic()
 for pos in range(0,len(items),8):
  admit('optimize',150);batch=[r for r in items[pos:pos+8]if not(CACHE/(r['key']+'.json')).exists()]
  if batch:
   request=[{'source_sha256':r['source_sha256'],'image_base64':base64.b64encode((DATASET_ROOT/r['path']).read_bytes()).decode()}for r in batch]
   results=worker.extract.remote(request,DEADLINES['optimize']);lookup={r['source_sha256']:r for r in batch}
   for r in results:
    item=lookup[r['source_sha256']];r['cache_key']=item['key'];r['observed_at']=now();atomic(CACHE/(item['key']+'.json'),r)
   done+=len(results)
  atomic(OUT/'observations/progress.json',{'time':now(),'scanned':min(pos+8,len(items)),'sources':len(items),'new_observations':done,'elapsed_seconds':time.monotonic()-start});print('observed',pos+len(batch),'/',len(items),flush=True)
 atomic(OUT/'observations/complete.json',{'time':now(),'sources':len(items),'new_observations':done,'elapsed_seconds':time.monotonic()-start})
if __name__=='__main__':main()
