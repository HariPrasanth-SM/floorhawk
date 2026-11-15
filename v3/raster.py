from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Configurable reference-parser adapter, reusing all original model/geometry code."""
import hashlib,json,time
from qa.common import ROOT,sha,write_json,inference_lock
from qa.raster import CubiParser
from v2.supervisor import fresh_host,Admission
PROFILES={'1024-one':[(0,0)],'1024-two':[(0,0),(2,2)]}
_parsers={}
def parse(file,profile='1024-one'):
 settings={'max_edge':1024,'rotations':PROFILES[profile],'threads':2,'ocr':False,'parser_source':sha(ROOT/'qa/raster.py'),'profile':profile};
 from demo_gpu import enabled,_last
 if enabled():settings['execution_policy']='host-auto-v1'
 h=sha(file);key=h+'-'+hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest();cache=CACHE_ROOT/'v3-raster'/(key+'.json');t=time.perf_counter()
 if cache.exists():
  r=json.loads(cache.read_text());r['cache_hit']=True;r['retrieval_seconds']=time.perf_counter()-t
  if r.get('execution'):_last.append(dict(r['execution'],cache_hit=True))
  return r
 if Admission().check(fresh_host())!='admit':raise RuntimeError('Resource admission paused')
 with inference_lock():
  if profile not in _parsers:_parsers[profile]=CubiParser('cpu',1024,rotations=PROFILES[profile],threads=2,ocr=False)
  facts=_parsers[profile].parse(file);facts.pop('_maps');facts.update(source_sha256=h,settings=settings,cache_hit=False,parse_seconds=time.perf_counter()-t);write_json(cache,facts);return facts
