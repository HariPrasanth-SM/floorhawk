from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Pinned external assets with an ownership ledger and conservative cleanup."""
import argparse,fcntl,hashlib,json,os,shutil,time,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;EXTERNAL=MODEL_ROOT;LEDGER=EXTERNAL/'downloads.jsonl'
CUBI_REV='c34440266665a11f4484eb06cd2e4b7d72ad76c1';QWEN_REV='89644892e4d85e24eaac8bacfd4f463576704203'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def ledger(path,url,purpose,state='retained'):
 EXTERNAL.mkdir(exist_ok=True)
 absolute=Path(path).absolute();name=str(absolute.relative_to(ROOT))if absolute.is_relative_to(ROOT)else str(absolute)
 entry={'path':name,'origin':url,'purpose':purpose,'state':state,'time':time.time(),'bytes':Path(path).stat().st_size if Path(path).exists() else 0,'sha256':sha(path) if Path(path).is_file() else None}
 with LEDGER.open('a') as f:fcntl.flock(f,fcntl.LOCK_EX);f.write(json.dumps(entry)+'\n')
def download(url,path,purpose):
 path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
 if path.exists():return path
 reserve=15*1024**3
 if shutil.disk_usage(ROOT).free<reserve+6*1024**3:raise RuntimeError('Insufficient disk reserve for download')
 part=path.with_suffix(path.suffix+'.part');ledger(part,url,purpose,'partial')
 try:
  with urllib.request.urlopen(url,timeout=60) as source,part.open('wb') as dest:
   while b:=source.read(1024*1024):dest.write(b)
  part.replace(path);ledger(path,url,purpose);return path
 except Exception:
  ledger(part,url,purpose,'failed_partial');raise

def cubi():
 url=f'https://codeload.github.com/CubiCasa/CubiCasa5k/zip/{CUBI_REV}'
 target=EXTERNAL/'cubicasa';target.mkdir(exist_ok=True)
 if not (target/'floortrans').exists():
  archive=download(url,EXTERNAL/'cubicasa-code.zip','official inference source archive')
  with zipfile.ZipFile(archive) as z:
   for member in z.infolist():
    relative=Path(*Path(member.filename).parts[1:]);dest=target/relative
    if not relative.parts:continue
    if '..' in relative.parts or member.external_attr>>16&0o170000==0o120000:raise ValueError('Unsafe archive member')
    if member.is_dir():dest.mkdir(parents=True,exist_ok=True)
    else:
     dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member));ledger(dest,url,'official source')
  ledger(archive,url,'verified extracted code archive','redundant_archive')
 weights=EXTERNAL/'cubicasa-model.pkl'
 if not weights.exists():
  import gdown
  url='https://drive.google.com/uc?id=1gRB7ez1e4H7a9Y09lLqRuna0luZO5VRK'
  ledger(weights,url,'official pretrained multi-task weights','pending')
  gdown.download(url,str(weights),use_cookies=False,quiet=False)
  if not weights.exists():raise RuntimeError('Official checkpoint download failed')
  ledger(weights,url,'official pretrained multi-task weights')
 print('CubiCasa checkpoint',weights,weights.stat().st_size,sha(weights),flush=True)

def qwen():
 target=EXTERNAL/'qwen3-vl-2b';target.mkdir(exist_ok=True)
 files=['README.md','config.json','generation_config.json','preprocessor_config.json','video_preprocessor_config.json','chat_template.json','merges.txt','vocab.json','tokenizer.json','tokenizer_config.json','model.safetensors']
 for name in files:
  url=f'https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/resolve/{QWEN_REV}/{name}';path=download(url,target/name,'Qwen3-VL local fallback');print(name,path.stat().st_size,flush=True)
 if sha(target/'model.safetensors')!='7de1838c87a5349b016c26a1c3f7d2bc400a3d485f95ef39a7059ffd734977a0':raise ValueError('Qwen upstream-pinned checkpoint checksum mismatch')
 (target/'provenance.json').write_text(json.dumps({'repository':'Qwen/Qwen3-VL-2B-Instruct','revision':QWEN_REV,'license':'Apache-2.0 as declared by model card','files':{n:sha(target/n) for n in files}},indent=2)+'\n')

def cleanup():
 if not LEDGER.exists():return
 latest={}
 for line in LEDGER.read_text().splitlines():
  entry=json.loads(line);latest[entry['path']]=entry
 total=0
 for name,entry in list(latest.items()):
  if entry.get('state','retained') not in ('redundant_archive','failed_partial'):continue
  path=ROOT/name
  allowed=EXTERNAL in path.absolute().parents or (CACHE_ROOT/'pip-qa') in path.absolute().parents or (CACHE_ROOT/'pip-v2') in path.absolute().parents
  if path.is_symlink() or not allowed or not path.is_file():continue
  if entry.get('sha256')!=sha(path) or entry.get('bytes')!=path.stat().st_size:continue
  if any(p.is_symlink() for p in path.parents if p!=ROOT.parent):continue
  size=path.stat().st_size;path.unlink();ledger(path,entry['origin'],entry['purpose'],f'deleted_reclaimed_{size}_bytes');total+=size
 print('Ledger-owned bytes reclaimed:',total)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('asset',choices=['cubi','qwen','cleanup']);a=p.parse_args();globals()[a.asset]()
