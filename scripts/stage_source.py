"""Explicit source allowlist, followed by staged-byte checks. Never stages assets."""
import subprocess,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
top=['AGENTS.md','STATUS.md','MORNING_HANDOFF.md','SOLUTION_ANALYTICS.md','presentation.py','custom_detector.py','cumulative_evidence.py','diagnostic_export.py','large_drawing.py','image_ingest.py','runtime_paths.py','app.py','legacy_server.py','qa_app.py','assets.py','detector.py','demo_gpu.py','vlm_worker.py','download_model.py','download_v2_assets.py','prepare_cubi_compat.py','run.py','evaluate.py','qa_score.py','qa_benchmark.py','qa_visualize.py','MODEL_REGISTRY.json','model.json','profiles.json','selected-profile.json','README.md','.gitignore','.env.example','ARTIFACTS.md','test_qa.py','test_v2.py','test_v3.py','test_demo_polish.py','test_inspection.py','test_geometry.py']
paths=[p for p in top if(ROOT/p).is_file()]
paths +=[p.name for p in ROOT.glob('requirements*.txt')]+[p.name for p in ROOT.glob('start*.sh')]
for folder in ['qa','v2','v3','inspection','iteration','evaluation','campaign','scripts','tests','config','docs','reports/history','web','deploy/modal']:
 for p in(ROOT/folder).rglob('*'):
  if p.is_file()and (p.suffix in['.py','.sh','.js','.css','.html','.md','.json']or p.name.startswith('LICENSE'))and '__pycache__'not in p.parts and p.name!='english-translations.json':paths.append(str(p.relative_to(ROOT)))
subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
files=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');bad=[]
for name in filter(None,files):
 raw=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
 if len(raw)>2_000_000 or any(x in name.split('/')for x in ['results','external','cache','datasets','benchmarks','.entire']):bad.append(name+': forbidden path/size')
 if re.search(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----',raw) or (b'/home/' + b'harry/')in raw:bad.append(name+': credential/private path pattern')
if bad:raise SystemExit('\n'.join(bad))
print('Staged source files reviewed:',len(list(filter(None,files))),'total bytes:',sum(len(subprocess.check_output(['git','show',':'+n],cwd=ROOT))for n in filter(None,files)))
