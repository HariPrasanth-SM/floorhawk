"""Answer-free closed-native-room area observations across development PDF sources."""
import json,time
from pathlib import Path
from qa.common import sha
from runtime_paths import DATASET_ROOT
from .clock import atomic,admit,now
from .pdf_quantities import recover
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115'
def main():
 paths=sorted({q['path']for q in(json.loads(l)for l in(ROOT/'benchmarks/qa-v3/quick.questions.jsonl').open())if q['path'].endswith('.pdf')});folder=OUT/'observations/pdf-prefixed-v3';folder.mkdir(exist_ok=True)
 for i,path in enumerate(paths):
  admit('optimize',20);source=sha(DATASET_ROOT/path);dest=folder/(source+'.json')
  if dest.exists():continue
  try:
   facts=recover(DATASET_ROOT/path);r={'source_sha256':source,'path':path,'status':'success','facts':facts}
  except Exception as e:r={'source_sha256':source,'path':path,'status':'failed','reason':str(e)[:120]}
  atomic(dest,r);print(i+1,len(paths),path,r['status'],len(r.get('facts',{}).get('closed_room_geometry_recovery',{}).get('recovered',[])),flush=True)
 atomic(folder/'complete.json',{'time':now(),'sources':len(paths)})
if __name__=='__main__':main()
