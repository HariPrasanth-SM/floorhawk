from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
import contextlib,fcntl,hashlib,importlib.metadata,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=CACHE_ROOT/'qa';CACHE.mkdir(parents=True,exist_ok=True)
VERSION='qa-2.0.0'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def versions():return {d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
def write_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
@contextlib.contextmanager
def inference_lock():
 with (CACHE_ROOT/'inference.lock').open('a') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise RuntimeError('Another local inference is running. Wait and retry.')
  yield

def bbox_union(items):
 return [min(b[0] for b in items),min(b[1] for b in items),max(b[2] for b in items),max(b[3] for b in items)]
def norm(s):
 import unicodedata,re
 return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(c))).strip()
