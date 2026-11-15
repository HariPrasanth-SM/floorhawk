"""Allowlisted verified runtime assets only; no company drawings or gold."""
import sys,json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from qa.common import sha
from runtime_paths import MODEL_ROOT,DATASET_ROOT
NAMES=['cubicasa-model.pkl','rtdetr/rtdetr_l_autoresearch_60ep.pt','rtdetr/revision.txt','v3-room-model/calibration.json','v3-wash-model/calibration.json','v3-layout-model/calibration.json','v3-weak-box/calibration.json','v3-cross-box/calibration.json','ppocr-v5/ch_ppocr_mobile_v2.0_cls_infer.onnx','ppocr-v5/latin_PP-OCRv5_rec_mobile_infer.onnx','ppocr-v5/ch_PP-OCRv5_mobile_det.onnx','ppocr-v5/provenance.json','cubicasa-compatible/patches.json']
def build():
 names=NAMES+[str(p.relative_to(MODEL_ROOT))for p in(MODEL_ROOT/'cubicasa-compatible/floortrans').rglob('*.py')]
 rows=[]
 for name in names:
  p=MODEL_ROOT/name
  if not p.is_file():raise FileNotFoundError(name)
  rows.append({'filename':name,'size':p.stat().st_size,'sha256':sha(p),'license':'CubiCasa CC BY-NC-SA4.0 / Ultralytics AGPL3; restricted research demo, no commercial-rights claim'if 'cubicasa'in name or'rtdetr'in name else'Existing project calibration or PaddleOCR Apache2; provenance retained','source':'https://github.com/CubiCasa/CubiCasa5k/tree/c34440266665a11f4484eb06cd2e4b7d72ad76c1'if 'cubicasa'in name else'Existing verified runtime; see v2/registry.json','purpose':'Enabled verified v3 route'})
 p=MODEL_ROOT/'cubicasa/LICENSE';rows.append({'filename':'licenses/CubiCasa-LICENSE','size':p.stat().st_size,'sha256':sha(p),'license':'Original upstream notice','source':'CubiCasa pinned source','purpose':'Third-party license'})
 return {'version':sha(ROOT/'v3/config.json')[:12]+'-'+hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()[:12],'models':rows,'samples':[],'omitted':['Company drawings and unreviewed dataset gallery omitted; operator uploads are private','Custom YOLO and Qwen are unpromoted/disabled and not uploaded']}
def source(row):return MODEL_ROOT/'cubicasa/LICENSE'if row['filename']=='licenses/CubiCasa-LICENSE'else MODEL_ROOT/row['filename']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--upload',action='store_true');a=p.parse_args();m=build();a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(m,indent=2))
 if a.upload:
  import modal
  volume=modal.Volume.from_name('floorhawk-assets',create_if_missing=True)
  missing=[]
  for r in m['models']:
   remote='/'+m['version']+'/'+r['filename']
   try:next(volume.read_file(remote));exists=True
   except (FileNotFoundError,Exception)as e:
    if type(e).__name__ not in ['NotFoundError','FileNotFoundError']:raise
    exists=False
   if not exists:missing.append(r)
  with volume.batch_upload()as batch:
   for r in missing:batch.put_file(source(r),'/'+m['version']+'/'+r['filename'])
   import io
   try:next(volume.read_file('/'+m['version']+'/assets.json'))
   except Exception:batch.put_file(io.BytesIO(json.dumps(m).encode()),'/'+m['version']+'/assets.json')
  print('Uploaded missing assets:',len(missing),'version:',m['version'])
 print('Manifest assets',len(m['models']),'bytes',sum(r['size']for r in m['models']))
