from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Bounded pinned assets from RapidOCR3.4.1's checked model manifest."""
import json,hashlib,time,urllib.request
from pathlib import Path
from .policy import ROOT
from qa.common import write_json,sha

def main():
 import rapidocr,yaml
 pkg=Path(rapidocr.__file__).parent;data=yaml.safe_load((pkg/'default_models.yaml').read_text())['onnxruntime']['PP-OCRv5'];out=MODEL_ROOT/'ppocr-v5';out.mkdir(exist_ok=True);records=[]
 for group,name in [('det','ch_PP-OCRv5_mobile_det.onnx'),('rec','latin_PP-OCRv5_rec_mobile_infer.onnx')]:
  choices=data[group]
  if name not in choices:
   if group=='det':name=next(k for k in choices if 'mobile' in k)
   else:raise ValueError('Pinned model manifest missing')
  info=choices[name];url=info['model_dir'];dest=out/name
  if not dest.exists():
   with urllib.request.urlopen(url,timeout=45) as r,dest.with_suffix('.partial').open('wb') as f:
    n=0
    while chunk:=r.read(1024**2):
     n+=len(chunk)
     if n>100*1024**2:raise ValueError('Asset exceeds bound')
     f.write(chunk)
   dest.with_suffix('.partial').replace(dest)
  if sha(dest)!=info['SHA256']:raise ValueError('OCR checkpoint hash mismatch')
  records.append({'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'size':dest.stat().st_size,'url':url,'purpose':'PP-OCRv5 CPU multilingual Latin OCR','retention':'selected-model','time':time.time()})
 # Classifier shipped in pinned wheel; explicitly copied and hashed, no auto-download.
 src=pkg/'models/ch_ppocr_mobile_v2.0_cls_infer.onnx';dest=out/src.name
 if not dest.exists():dest.write_bytes(src.read_bytes())
 records.append({'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'size':dest.stat().st_size,'url':'rapidocr3.4.1 wheel embedded asset','retention':'selected-model','purpose':'text orientation classifier'})
 write_json(out/'provenance.json',{'version':'RapidOCR3.4.1','assets':records,'model_source':'PaddleOCR, ONNX conversion RapidAI','license':'PaddleOCR Apache2.0 / RapidOCR Apache2.0, preserve upstream notices','language_claim':'Latin model; actual Finnish glyph tests separate from supported-character claims'})
 with (MODEL_ROOT/'downloads.jsonl').open('a') as f:
  for r in records:f.write(json.dumps(r)+'\n')
 print(json.dumps(records))
if __name__=='__main__':main()
