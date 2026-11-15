"""CPU-only OCR observations with fresh CPU/RAM/disk admission; no host CUDA needed."""
import json,time
from pathlib import Path
from runtime_paths import DATASET_ROOT
from .clock import admit,atomic,now
from .review_run import scan
import v2.ocr as ocr
from v2.supervisor import sample
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 ocr.fresh_host=lambda:sample(gpu=False);manifest=json.loads((OUT/'observations/manifest.json').read_text())['sources'];seen=scan('cache/v2-ocr',{r['source_sha256']for r in manifest});done=0
 for i,r in enumerate(manifest):
  if r['source_sha256']in seen:continue
  admit('optimize',45)
  try:result=ocr.parse(DATASET_ROOT/r['path']);done+=1;status='success'
  except Exception as e:status=type(e).__name__
  atomic(OUT/'observations/ocr-progress.json',{'time':now(),'new_ocr_sources':done,'last_index':i,'status':status});print(i,r['source_sha256'][:8],status,flush=True)
 atomic(OUT/'observations/ocr-complete.json',{'time':now(),'new_ocr_sources':done,'previous_sources':len(seen)})
if __name__=='__main__':main()
