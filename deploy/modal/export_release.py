"""Immutable allowlisted commit exporter; operational output is never tracked."""
import argparse,hashlib,json,subprocess,shutil,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
API='floorhawk.jobs.v1'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def export(commit,out,mode='full',frontend=None,extra_assets=None):
 commit=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
 if out.exists():raise ValueError('Release destination exists; immutable snapshots are never overwritten')
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit],cwd=ROOT,text=True).splitlines();out.mkdir(parents=True)
 allowed=[]
 for name in paths:
  p=Path(name)
  if p.name in ['gallery_prepare.py','presenter_prepare.py']:continue
  if p.parts[0]in ['qa','v2','v3','iteration','inspection','web','config','deploy','campaign']or len(p.parts)==1 and(p.name in ['app.py','legacy_server.py','qa_app.py','assets.py','detector.py','demo_gpu.py','vlm_worker.py','runtime_paths.py','image_ingest.py','large_drawing.py','cumulative_evidence.py','custom_detector.py','diagnostic_export.py','presentation.py','MODEL_REGISTRY.json','model.json','profiles.json','selected-profile.json']or p.name.startswith(('requirements','LICENSE'))):
   if p.suffix not in ['.py','.json','.txt','.js','.css','.html','.md','.sh']and not p.name.startswith('LICENSE')or '__pycache__'in p.parts:continue
   if p.parts[0]in ['config']and p.name in ['exploratory-exclusions.json']:continue
   raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
   if re.search(rb'/home/[a-z][a-z0-9_-]*/',raw) or re.search(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}',raw):raise ValueError('Private path/credential pattern: '+name)
   dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);allowed.append(name)
 if mode=='backend':
  if frontend is None:raise ValueError('Backend-only requires explicit prior release frontend')
  previous=json.loads((frontend/'release.json').read_text())
  if previous['api_contract']!=API:raise ValueError('Incompatible frontend API contract')
  shutil.rmtree(out/'web');shutil.copytree(frontend/'web',out/'web')
 asset_manifest=ROOT.parent/'floorhawk-modal/assets.json'
 if asset_manifest.is_file():shutil.copy2(asset_manifest,out/'assets.json')
 if extra_assets:
  extra=json.loads(Path(extra_assets).read_text())
  if not isinstance(extra,list):raise ValueError('Extra assets must be an allowlisted list')
  for row in extra:
   if Path(row['local_source']).is_absolute()or'..'in Path(row['local_source']).parts:raise ValueError('Asset source must be workspace-relative')
   if not re.fullmatch('[a-f0-9]{64}',row['sha256']):raise ValueError('Asset checksum required')
  (out/'extra-assets.json').write_text(json.dumps(extra,indent=2))
 files={str(p.relative_to(out)):digest(p.read_bytes())for p in out.rglob('*')if p.is_file()};front=digest(json.dumps({k:v for k,v in files.items()if k.startswith('web/')},sort_keys=True).encode())
 manifest={'source_commit':commit,'api_contract':API,'frontend_sha256':front,'frontend_source':str(frontend.name)if frontend else commit,'mode':mode,'files':files,'pipeline_configuration':json.loads((out/'v3/config.json').read_text()),'candidate_cumulative_enabled':False}
 (out/'release.json').write_text(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['full','backend'],default='full');p.add_argument('--frontend',type=Path);p.add_argument('--extra-assets',type=Path);a=p.parse_args();print(json.dumps(export(a.commit,a.output,a.mode,a.frontend,a.extra_assets),indent=2)[:500])
