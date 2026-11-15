"""Allowlisted deployed inventory and Apache-licensed OCR-only ZIP. No uploads."""
import json,hashlib,zipfile,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_paths import MODEL_ROOT
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'floorhawk-modal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def role_for(n):
 if n=='cubicasa-model.pkl':return 'Room/icon heatmaps and floor-plan segmentation'
 if n.startswith('cubicasa-compatible/'):return 'Pinned CubiCasa compatibility source and patch provenance'
 if n.startswith('rtdetr/'):return 'Structural door/window detector or its revision provenance'
 if n.startswith('v3-'):return 'Existing '+n.split('/')[0]+' calibration'
 if n.endswith('_cls_infer.onnx'):return 'Text orientation classification'
 if 'rec_'in n:return 'Latin text recognition'
 if n.endswith('_det.onnx'):return 'Text-region detection'
 if 'provenance'in n:return 'OCR source URL/hash provenance'
 return 'Required upstream license notice'
def main():
 base=json.loads((WORK/'assets.json').read_text());existing={r['filename']:r for r in json.loads((ROOT/'config/artifacts.json').read_text())['artifacts']};provenance=json.loads((MODEL_ROOT/'ppocr-v5/provenance.json').read_text());ocr={Path(x['path']).name:x for x in provenance['assets']};rows=[];paths={}
 for e in base['models']:
  n=e['filename'];e=dict(e,purpose=role_for(n));p=MODEL_ROOT/n if n!='licenses/CubiCasa-LICENSE'else MODEL_ROOT/'cubicasa/LICENSE';assert p.stat().st_size==e['size']and sha(p)==e['sha256'];m=existing.get(n,{});is_ocr=n.startswith('ppocr-v5/')and n.endswith('.onnx');r={'filename':n,'bytes':e['size'],'sha256':e['sha256'],'source':m.get('source',ocr.get(Path(n).name,{}).get('url',e['source'])),'revision':m.get('revision','RapidOCR3.4.1 / model manifest v3.4.0'if n.startswith('ppocr-v5/')else 'Pinned asset volume '+base['version']),'role':e['purpose'],'license':'Apache-2.0'if is_ocr else m.get('license',e['license']),'included_in_zip':is_ocr,'restore':'Use upstream source or authenticated Modal volume '+base['version']+'/'+n};rows.append(r);paths[n]=p
 for n in ['campaign-assets-v1/floorplan_yolo11m.pt','campaign-release-assets/568decc669d2ce00ed71f9f0cd0345dfedda5f2302293acb9d7777e0333c0c69/selector.json']:
  e=existing[n];p=ROOT.parent/'floorplan_detector/floorplan_yolo11m.pt'if n.endswith('.pt')else ROOT/'results/overnight-20261115/deployment-selector.json';assert p.stat().st_size==e['bytes']and sha(p)==e['sha256'];rows.append(dict(e,role='Frozen fixture/opening specialist'if n.endswith('.pt')else 'Frozen proposal selector',included_in_zip=False,restore='Authenticated Modal floorhawk-assets/'+n))
 manifest={'schema':1,'deployed_inference':'5827eab','standard_asset_version':base['version'],'assets':rows,'exclusions':'No datasets, drawings, references, predictions, secrets, caches, venvs or transcripts. Restricted/unclear weights/calibrations excluded.','drive_upload':'No authorized Drive upload tool available; manual upload only.'};dest=WORK/'handoff/event-readiness';dest.mkdir(parents=True,exist_ok=True);archive=dest/'floorhawk-redistributable-ocr.zip';assert not archive.exists(),'Preserve existing package';needed=sum(r['bytes']for r in rows if r['included_in_zip']);assert shutil.disk_usage(dest).free>needed*3+1024**3
 license_path=next((ROOT/'.venv/lib/python3.10/site-packages').glob('transformers-*.dist-info/licenses/LICENSE'));license_text=license_path.read_text();license_text=license_text[license_text.index('                                 Apache License'):];notice='Copyright (c) 2021 RapidOCR Authors. All rights reserved.\nCopyright (c) 2016 PaddlePaddle Authors. All Rights Reserved.\nUnmodified PP-OCR ONNX assets from the recorded sources.\nhttps://github.com/RapidAI/RapidOCR\nhttps://github.com/PaddlePaddle/PaddleOCR\nUpstream Apache2 licenses verified; original model hashes retained.\n'
 restore="# Restore FloorHAWK assets\n\nThis ZIP contains only the three recorded Apache-2.0 PP-OCR ONNX files, license/notices and inventory. It is NOT the complete model bundle. Verify each entry SHA256 against manifest.json before restoring below PROOFPLAN_MODEL_ROOT. Preserve paths under ppocr-v5/.\n\nAll other required assets are excluded because redistribution is restricted or insufficiently established. Use recorded upstream URLs or authenticated Modal restoration. Example:\n\n    .venv/bin/modal volume get floorhawk-assets /a18a52dae0e7-3ec800c811f2/cubicasa-model.pkl external/cubicasa-model.pkl\n\nCustom YOLO and selector paths, sizes and hashes are in manifest.json. No public redistribution right is granted for them. Restore upstream model/code licenses and the existing account's external secrets/accounting separately; no credentials or datasets are in this package. See the source repository ARTIFACTS.md.\n"
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(ROOT/'config/deployed-assets.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as z:
  for r in rows:
   if r['included_in_zip']:z.write(paths[r['filename']],r['filename'])
  z.writestr('manifest.json',json.dumps(manifest,indent=2));z.writestr('RESTORE.md',restore);z.writestr('licenses/Apache-2.0.txt',license_text);z.writestr('NOTICE.txt',notice)
 expected={r['filename']for r in rows if r['included_in_zip']}|{'manifest.json','RESTORE.md','licenses/Apache-2.0.txt','NOTICE.txt'}
 with zipfile.ZipFile(archive)as z:
  assert set(z.namelist())==expected and z.testzip()is None
  for r in rows:
   if r['included_in_zip']:assert hashlib.sha256(z.read(r['filename'])).hexdigest()==r['sha256']
 result={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'inventory_assets':len(rows),'included_model_files':sum(r['included_in_zip']for r in rows),'verified_entries':len(expected),'uploaded':False};(dest/'package-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
