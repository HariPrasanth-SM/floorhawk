"""Optional loopback-only local worker. No cloud inference adapter is enabled."""
import base64,json,urllib.request,urllib.parse,time
from pathlib import Path
class CloudAdapter:
 enabled=False
 def answer(self,*args,**kwargs):raise RuntimeError('Cloud inference is disabled; no automatic uploads are allowed')
class LocalVLM:
 def __init__(self,url):
  parsed=urllib.parse.urlparse(url)
  if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.path not in ('','/'):raise ValueError('VLM worker must be a loopback HTTP URL')
  self.url=url.rstrip('/')
 def health(self):
  try:return json.loads(urllib.request.urlopen(self.url+'/health',timeout=2).read())
  except Exception as e:return {'ready':False,'error':str(e)}
 def route(self,question):
  from .common import CACHE,write_json
  import hashlib
  revision=self.health().get('revision','unknown');key=hashlib.sha256((question+revision+'registered-router-v1').encode()).hexdigest();cache=CACHE/('vlm-route-'+key+'.json')
  if cache.exists():return json.loads(cache.read_text())
  data=json.dumps({'mode':'route','question':question}).encode();request=urllib.request.Request(self.url+'/answer',data=data,headers={'Content-Type':'application/json'});response=json.loads(urllib.request.urlopen(request,timeout=180).read())
  if response.get('status')=='success':write_json(cache,response)
  return response
 def answer(self,path,question,task,facts):
  from PIL import Image,ImageOps
  from .common import CACHE,sha,write_json
  import io,pymupdf,hashlib
  if Path(path).suffix.lower()=='.ifc':return {'status':'unsupported','answer':None,'unit':None,'evidence':[],'warnings':['VLM cannot inspect hidden IFC properties from a screenshot']}
  if task['operation']!='count' or task['target']=='unknown':return {'status':'abstained','answer':None,'unit':None,'evidence':[],'warnings':['Direct visual physical quantities/text require grounded tool evidence; no unsupported numeric fallback.']}
  if Path(path).suffix.lower()=='.pdf':
   doc=pymupdf.open(path)
   if task['scope']=='model' or len(doc)!=1:return {'status':'abstained','answer':None,'unit':None,'evidence':[],'warnings':['One rasterized page cannot establish whole-model or multipage completeness.']}
   pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(.7,.7));im=Image.open(io.BytesIO(pix.tobytes('png')))
  else:im=ImageOps.exif_transpose(Image.open(path)).convert('RGB')
  health=self.health();revision=health.get('revision','unknown')
  key=hashlib.sha256((sha(path)+revision+facts.get('preprocessing_version','')+'inventory-v1-max768-pixels262144').encode()).hexdigest();cache=CACHE/('vlm-inventory-'+key+'.json')
  cached=cache.exists()
  if cached:response=json.loads(cache.read_text())
  else:
   im.thumbnail((768,768));buf=io.BytesIO();im.save(buf,format='PNG')
   body={'mode':'inventory','image_base64':base64.b64encode(buf.getvalue()).decode(),'evidence':[{'id':e['id'],'class':e.get('class'),'label':e.get('label'),'area_m2':e.get('area_m2')} for e in facts.get('entities',[])][:60]}
   request=urllib.request.Request(self.url+'/answer',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'});response=json.loads(urllib.request.urlopen(request,timeout=180).read())
   if response.get('status') in ('success','abstained'):write_json(cache,response)
  if response.get('status') not in ('success','abstained'):return response
  value=response.get('counts',{}).get(task['target'])
  if value is None:return {'status':'abstained','answer':None,'unit':None,'evidence':[],'warnings':['The local visual inventory did not provide this target.']}
  if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError('Invalid local VLM count')
  return {'status':'success','answer':value,'answer_type':'number','unit':'count','route':'vlm.local.ungrounded','evidence':[],'grounding':'ungrounded direct visual inventory estimate','count_semantics':'estimate','calculation_trace':[{'operation':'select_target_from_cached_visual_inventory','target':task['target'],'value':value,'image_encoding_cache_hit':cached}],'model':response.get('model'),'peak_gpu_memory_bytes':response.get('peak_gpu_memory_bytes'),'vlm_timing':{'cache_hit':cached,'worker':response.get('timing') if not cached else None},'warnings':response.get('warnings',[])+['No localization or completeness proof; one visual inventory is reused across questions/translations.']}
