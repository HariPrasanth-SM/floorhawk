"""Generate exact allowlisted artifact manifest; optionally package custom assets only."""
import argparse,json,tarfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathlib import Path
from runtime_paths import MODEL_ROOT,RESULTS_ROOT
from qa.common import ROOT,sha,write_json
SPEC=[('cubicasa-model.pkl','third_party','https://drive.google.com/uc?id=1gRB7ez1e4H7a9Y09lLqRuna0luZO5VRK','c34440266665a11f4484eb06cd2e4b7d72ad76c1','CC BY-NC4.0 upstream; commercial use not inferred'),('rtdetr/rtdetr_l_autoresearch_60ep.pt','third_party','https://raw.githubusercontent.com/OldDeLorean/rtdetr-floorplan-detector/8ef73f8c42e35f4a4c42a9e2db643ca115531e5f/weights/rtdetr_l_autoresearch_60ep.pt','8ef73f8c42e35f4a4c42a9e2db643ca115531e5f','See pinned v2 registry; redistribution requires license review'),('v3-room-model/calibration.json','custom','local bounded count supervision','frozen v3','Research artifact; underlying data/weights restrictions apply'),('v3-wash-model/calibration.json','custom','local bounded count supervision','frozen v3','Research artifact; underlying data/weights restrictions apply'),('v3-layout-model/calibration.json','custom','local bounded count supervision','frozen v3','Research artifact; underlying data/weights restrictions apply')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--package-custom',action='store_true');a=p.parse_args();entries=[]
 for name,kind,source,revision,license in SPEC:
  f=MODEL_ROOT/name
  if not f.is_file():raise ValueError('Required artifact missing: '+name)
  entries.append({'filename':name,'kind':kind,'bytes':f.stat().st_size,'sha256':sha(f),'source':source,'revision':revision,'license':license})
 write_json(ROOT/'config/artifacts.json',{'schema':1,'artifacts':entries,'note':'No construction datasets, drawings, secrets, predictions or transcripts permitted. Optional Qwen/OCR/source compatibility assets restore via existing pinned downloaders and registries.'})
 if a.package_custom:
  out=RESULTS_ROOT/'iteration60/custom-artifacts.tar.gz';out.parent.mkdir(exist_ok=True,parents=True)
  if out.exists():raise ValueError('Preserve existing archive; choose another explicit task output')
  with tarfile.open(out,'w:gz')as t:
   for e in entries:
    if e['kind']=='custom':t.add(MODEL_ROOT/e['filename'],arcname=e['filename'])
  write_json(out.with_suffix('.sha256.json'),{'filename':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'uploaded':False})
 print('Artifact manifest ready; custom packaging requested:',a.package_custom)
if __name__=='__main__':main()
