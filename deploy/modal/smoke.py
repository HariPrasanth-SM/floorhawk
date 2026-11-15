"""Private protected browser smoke; source files only, no evaluation references."""
import os,sys,json,time,base64,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from runtime_paths import DATASET_ROOT,RESULTS_ROOT
from v2.budget import Ledger
from qa.common import write_json
import modal
from playwright.sync_api import sync_playwright
WORK=ROOT.parent/'floorhawk-modal';URL='https://sm-hariprasanth--web.us-east.modal.run';O=WORK/'verification';O.mkdir(exist_ok=True);secrets_dir=WORK/'.secrets';state=modal.Dict.from_name('floorhawk-control-v1');before=Ledger().summary();report={'passed':False,'url':URL,'jobs':[]};errors=[];started=time.monotonic();stop=time.time()+900
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
def wait(page,expr,seconds=400):
 end=min(stop,time.time()+seconds)
 while time.time()<end:
  if page.evaluate(expr):return
  page.wait_for_timeout(300)
 raise AssertionError('Timeout '+expr+' '+page.inner_text('#status'))
def probe(sid):
 if not state.put('admission-lock-v1','verification-controller',skip_if_exists=True):raise RuntimeError('Admission locked; refusing recovery')
 try:
  s=state.get('admission-state-v1');s['verification_sessions']=[sid];state.put('admission-state-v1',s)
 finally:state.pop('admission-lock-v1',None)
try:
 with sync_playwright()as p:
  b=p.chromium.launch(headless=True);saved=secrets_dir/'cloud-browser-state.json';context=b.new_context(viewport={'width':1366,'height':768},storage_state=str(saved)if saved.exists()else None);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL)
  if page.locator('input[name=code]').count():page.fill('input[name=code]',(secrets_dir/'event-access-code').read_text());page.click('button');page.wait_for_url(URL+'/')
  wait(page,"() => typeof S!=='undefined' && !!S.config",60)
  sid=next(c['value'].split('.')[0]for c in context.cookies()if c['name']=='floorhawk-session');probe(sid);context.storage_state(path=str(saved));saved.chmod(0o600)
  health=page.request.get(URL+'/health').json();report['health_before']=health;assert not health['live'];assert not health['gemini']
  other=b.new_context();other_page=other.new_page();other_page.goto(URL);assert other_page.locator('input[name=code]').is_visible();assert other.request.get(URL+'/api/config').status==401
  first=DATASET_ROOT/'data/cubicasa5k/colorful-10052.png';second=DATASET_ROOT/'data/cubicasa5k/high_quality-13847.png'
  cases=[(first,'How many windows are shown on this floor plan?'),(first,'How many doors are shown on this floor plan?'),(second,'How many windows are shown on this floor plan?')]
  for i,(source,question)in enumerate(cases):
   if time.time()>stop-430:raise RuntimeError('Stop launching billable tests near local deadline')
   idem='floorhawk-cloud-smoke-'+str(i);capture=[]
   def route(req):
    if req.request.method=='POST':
     capture.append(req.request.post_data);headers=dict(req.request.headers);headers['Idempotency-Key']=idem;req.continue_(headers=headers)
    else:req.continue_()
   page.route('**/api/jobs',route);page.set_input_files('#upload',str(source));page.fill('#question',question);page.click('#run');page.wait_for_timeout(500)
   if not capture:raise AssertionError('No upload request')
   # The duplicate uses the exact idempotency key; it must not create a second job.
   duplicate=page.request.post(URL+'/api/jobs',data=capture[0],headers={'Content-Type':'application/json','Idempotency-Key':idem});assert duplicate.status==202;job_id=duplicate.json()['id'];report['duplicate_id_'+str(i)]=job_id
   assert other.request.get(URL+'/api/jobs/'+job_id).status==401
   wait(page,"() => !S.busy && S.job?.status==='success'",400);job=page.evaluate('S.job');assert job['id']==job_id
   pred=job['prediction'];assert pred['status']=='success',pred.get('warnings');assert pred['evidence'];assert any(e.get('device')=='cuda:0'and'cuda:0'in e.get('observed_tensor_devices',[])for e in pred.get('live_execution',[])),pred.get('live_execution');assert page.evaluate('S.boxes.length>0');wait(page,"() => !document.getElementById('highResCrop').hidden",45)
   assert 'paired'not in pred;assert page.locator('#groundTruthPanel').is_hidden();report['jobs'].append({'id':job_id,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'question':question,'answer':pred['answer'],'evidence_n':len(pred['evidence']),'execution':pred['live_execution'],'release':job.get('release',{}).get('source_commit'),'timing':pred.get('timing')});write_json(O/('job-'+str(i)+'.json'),job);page.unroute('**/api/jobs',route)
  # Authenticated second visitor cannot inspect the first visitor's artifacts.
  other_page.fill('input[name=code]',(secrets_dir/'event-access-code').read_text());other_page.click('button');other_page.wait_for_url(URL+'/');assert other.request.get(URL+'/api/jobs/'+report['jobs'][0]['id']).status==404;report['session_isolation']=True
  # Third distinct upload hits the deployed two-upload quota without dispatching inference.
  invalid={'file_name':'third.png','file_base64':base64.b64encode(b'new distinct bytes').decode(),'question':'Count windows','mode':'local'};response=page.request.post(URL+'/api/jobs',data=invalid);assert response.status==429;assert 'Upload allowance'in response.json()['error'];report['upload_quota']=True
  page.reload();wait(page,"() => !!S.job",45);assert page.evaluate('S.job.id')==report['jobs'][-1]['id'];report['reload_no_resubmit']=True
  for w,h in [(1366,768),(1920,1080)]:
   page.set_viewport_size({'width':w,'height':h});assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
  report['allowance']=page.request.get(URL+'/api/allowance').json();assert report['allowance']['questions_remaining']==2;assert not errors;report['browser_errors']=errors;report['local_no_gemini_calls']=Ledger().summary()==before;assert report['local_no_gemini_calls'];report['passed']=True;report['seconds']=time.monotonic()-started;context.storage_state(path=str(saved));b.close()
finally:
 write_json(O/'cloud-smoke.json',report);print(json.dumps(report,indent=2))
