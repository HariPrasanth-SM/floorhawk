"""Local synthetic browser contract checks; no model/provider calls. Run from proofplan/."""
import os,sys,json,time,threading,io,tempfile
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];(ROOT/'results/agile-ui').mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(ROOT));os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
buf=io.BytesIO();Image.new('RGB',(300,200),'white').save(buf,format='PNG');PNG=buf.getvalue()
LOCAL={'status':'success','answer':6,'unit':'count','evidence':[{'id':'room-1','label':'Korridor','bbox':[10,20,80,70],'page':1,'method':'native PDF text','provenance':'Parsed numbered room registry'}],'task':{'operation':'count','target':'room'},'route':'pdf.native','timing':{'total_seconds':.1},'device':'cpu','warnings':['Extracted labels; completeness needs review.']}
def job(id,mode='hybrid',failure=None):
 import copy
 local=copy.deepcopy(LOCAL);hybrid={'status':failure or'success','answer':None if failure else 4,'unit':'count','evidence_ids':['room-1'],'explanation':'Review of supplied source evidence.','generation':[{'model':'gemini-fixture'}],'provider_attempts':0,'timing':{'additional_gemini_seconds':.2}}
 pred=copy.deepcopy(local)
 if mode=='hybrid':pred['paired']={'local':local,'hybrid':hybrid}
 return {'id':id,'mode':mode,'status':'success','stage':'Answer ready','source_name':'synthetic-fixture.png','input_kind':'image','question':'How many corridors?','credit':'Synthetic browser fixture; no inference','pages':[{'page':1,'width':300,'height':200}],'prediction':pred,'review':{'revision':0,'boxes':[{'xyxy':[10,20,80,70],'page':1,'included':True,'evidence_id':'room-1','class_name':'room'}],'included_evidence_ids':['room-1'],'answer':6,'unit':'count','reviewed_count':6,'instance_count':False,'reviewed':False},'progress':1}
state={'mode':'local','gets':0,'posts':[],'counter':0}
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,value,mime='application/json'):
  raw=value if isinstance(value,bytes)else json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type',mime);self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  p=self.path.split('?')[0]
  if p=='/api/config':return self.send({'ready':True,'diagnostics':True,'paired':True,'token':'fixture','samples':[],'host_vision':True,'cloud':{'default_mode':'local'}})
  if p=='/api/budget':return self.send({'requests_reserved':0,'requests_max':1000,'estimated_usd_reserved':0,'estimated_usd_max':10})
  if p in ['/','/app.js','/style.css']:return self.send((ROOT/'web'/('index.html'if p=='/'else p[1:])).read_bytes(),'text/html'if p=='/'else'application/javascript'if p.endswith('.js')else'text/css')
  if p.endswith(('/image','/crop.png'))or'/page/'in p:return self.send(PNG,'image/png')
  if p.endswith('/presentation'):return self.send({'evidence':[dict(LOCAL['evidence'][0],id='hybrid-only',origin_model='custom_yolo')],'boxes':[{'xyxy':[90,30,140,80],'included':True,'page':1,'evidence_id':'hybrid-only','class_name':'window'}]})
  if p.startswith('/api/jobs/'):
   id=p.split('/')[3];state['gets']+=1;j=job(id,state['mode'])
   if state['gets']==1 and state['mode']=='hybrid':j.update(status='running',stage='Local ready',local_prediction=LOCAL,local_review=j['review'])
   return self.send(j)
  return self.send({})
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));state['posts'].append((self.path,data))
  if self.path=='/api/cloud-state':return self.send({'note':'Fixture mode selected'})
  if self.path=='/api/jobs':state.update(mode=data['mode'],gets=0,counter=state['counter']+1);return self.send({'id':'fixture-'+str(state['counter'])})
  return self.send({})
server=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=server.serve_forever,daemon=True).start();checks={};errors=[]
def check(k,v):checks[k]=bool(v);assert v,k
def wait(page,expr):
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  if page.evaluate(expr):return
  page.wait_for_timeout(30)
 raise AssertionError(expr+' '+page.inner_text('#status'))
with tempfile.TemporaryDirectory()as d,sync_playwright()as p:
 f=Path(d)/'fixture.png';f.write_bytes(PNG);b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1366,'height':768});page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port));wait(page,'() => !!S.config');check('initial_ask_disabled',page.locator('#run').is_disabled());page.set_input_files('#upload',str(f));check('empty_prompt_disabled',page.locator('#run').is_disabled());page.fill('#question','How many corridors?');check('both_enable_ask',page.locator('#run').is_enabled());page.click('#clearQuestion');check('clear_prompt_disables',page.locator('#run').is_disabled());page.fill('#question','How many corridors?');page.click('#clearImage');check('clear_image_disables',page.locator('#run').is_disabled());page.set_input_files('#upload',str(f));page.fill('#question','How many corridors?');page.check('#geminiToggle');page.click('#run');wait(page,'() => S.partialDisplayed===true');page.uncheck('#geminiToggle');wait(page,'() => !S.busy && !!S.job?.prediction?.paired');check('submitted_hybrid_stays_hybrid',page.inner_text('#modelCount')=='4 count');check('primary_label',page.inner_text('#answerSource')=='Hybrid review');check('local_hidden_default',not page.locator('#pairedLocalRow').is_visible());wait(page,"() => S.boxes[0]?.evidence_id==='hybrid-only'");check('hybrid_boxes_selected',page.evaluate("S.boxes[0].xyxy[0]===90"));check('hybrid_crop_source','custom_yolo'in page.inner_text('#cropCaption'));check('export_on_top',page.locator('header #exportDiagnostic').count()==1);page.check('#showLocalAnswer');check('explicit_local_switch',page.inner_text('#modelCount')=='6 count');check('provenance_visible','native PDF text'in page.inner_text('#evidenceTable'));check('live_sample_hidden',not page.locator('#sampleSelect').is_visible());check('diagnostic_link',page.locator('#exportDiagnostic').get_attribute('href').endswith('/diagnostic.zip'));page.click('#diagnosticsButton');check('diagnostic_actual_review','gemini-fixture'in page.inner_text('#diagnosticSteps'));page.click('#closeDiagnostics')
 for w,h in [(1366,768),(1920,1080)]:page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(100);check('viewport_'+str(w),page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'))
 # Real frontend state switch checks with explicit fixture responses, never provider calls.
 page.evaluate("() => {S.job="+json.dumps(job('fail','hybrid','provider_error'))+";S.showLocal=false;renderPaired(S.job)}");check('failed_hybrid_local_fallback',page.inner_text('#modelCount')=='6 count'and'fallback'in page.inner_text('#answerSource'))
 page.evaluate("() => {S.job="+json.dumps(job('abstain','hybrid','abstained'))+";S.showLocal=false;renderPaired(S.job)}");check('abstained_not_local_fallback',page.inner_text('#modelCount')=='—'and page.inner_text('#answerStatus')=='ABSTAINED')
 f2=Path(d)/'second.png';f2.write_bytes(PNG);page.set_input_files('#upload',str(f2));check('document_switch_clears_old_answer',page.inner_text('#modelCount')=='—');check('document_switch_clears_evidence',page.inner_text('#evidenceTable')=='');check('no_page_errors',not errors);page.screenshot(path=str(ROOT/'results/agile-ui/fixture-browser.png'));checks['errors']=errors;(ROOT/'results/agile-ui/verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2));b.close()
server.shutdown();server.server_close()
