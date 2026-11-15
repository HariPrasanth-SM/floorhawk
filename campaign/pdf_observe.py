"""Answer-free native PDF geometry source pass; no reference or model association."""
import json,time
from pathlib import Path
from qa.common import sha
from runtime_paths import DATASET_ROOT
from .clock import atomic,admit,now
from .pdf_doors import parse,VERSION
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 qs=[json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.questions.jsonl').open()];paths=sorted({r['path']for r in qs if r['path'].endswith('.pdf')});folder=OUT/'observations/pdf-doors';folder.mkdir(exist_ok=True)
 for i,path in enumerate(paths):
  admit('optimize',20);source=sha(DATASET_ROOT/path);dest=folder/(source+'.json')
  if dest.exists():continue
  t=time.monotonic()
  try:r=parse(DATASET_ROOT/path);r.update(path=path,seconds=time.monotonic()-t)
  except Exception as e:r={'status':'unsupported','source_sha256':source,'path':path,'reason':type(e).__name__+': '+str(e)[:120]}
  atomic(dest,r);print(i+1,len(paths),path,r['status'],len(r.get('entities',[])),flush=True)
 atomic(folder/'complete.json',{'time':now(),'sources':len(paths),'version':VERSION})
if __name__=='__main__':main()
