"""Bounded real local/paired upload smoke; never reads reference answers."""
import sys,os,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,write_json
from runtime_paths import RESULTS_ROOT,DATASET_ROOT
from v2.budget import Ledger
from playwright.sync_api import sync_playwright
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright');O=RESULTS_ROOT/'iteration60';checks={};errors=[];seen_local=[]
def check(name,value):
 checks[name]=bool(value)
 if not value:raise AssertionError(name)
def wait(page,expr,timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if page.evaluate(expr):return
  page.wait_for_timeout(150)
 raise AssertionError('Timeout '+expr+' '+page.inner_text('#status'))
q=next(q for q in map(json.loads,(O/'questions.jsonl').open())if q['path'].endswith('.png'))
with sync_playwright()as p:
 browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1366,'height':768});page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text)if m.type=='error'else None)
 def response(r):
  if '/api/jobs/'in r.url and r.request.method=='GET'and r.headers.get('content-type','').startswith('application/json'):
   try:
    data=r.json()
    if data.get('local_prediction')and data.get('status')=='running':seen_local.append(data['id'])
   except Exception:pass
 page.on('response',response);page.goto('http://127.0.0.1:8773');wait(page,'() => S.config?.paired===true');check('candidate_flag',True);before=Ledger().summary();page.set_input_files('#upload',str(DATASET_ROOT/q['path']));page.fill('#question',q['question']);page.click('#run');wait(page,"() => !S.busy && S.job?.status==='success'");local=page.evaluate('S.job');check('local_no_provider',Ledger().summary()['requests_reserved']==before['requests_reserved']);check('local_answer_saved',local['prediction'].get('answer')is not None);check('no_live_reference',not page.locator('#groundTruthPanel').is_visible());page.select_option('#executionMode','hybrid');page.wait_for_timeout(200);page.click('#run');wait(page,"() => !S.busy && !!S.job?.prediction?.paired",180);job=page.evaluate('S.job');check('progressive_local_seen',bool(seen_local));check('separate_answers',page.locator('#pairedLocal').is_visible()and page.locator('#pairedHybrid').is_visible());check('local_survives',job['prediction']['paired']['local']['answer']==local['prediction']['answer']);check('same_bundle',job['prediction']['paired']['hybrid'].get('shared_evidence_sha256')==job['prediction']['shared_evidence']['sha256']);check('bounded_calls',0<=Ledger().summary()['requests_reserved']-before['requests_reserved']<=2);checks['hybrid_status']=job['prediction']['paired']['hybrid']['status'];checks['provider_attempts']=job['prediction']['paired']['hybrid'].get('provider_attempts',0);checks['job_id']=job['id'];page.screenshot(path=str(O/'paired-live-smoke.png'))
 for w,h in [(1366,768),(1920,1080)]:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(180);check('live_viewport_'+str(w),page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'))
 page.click('#diagnosticsButton');check('diagnostics',page.locator('#diagnostics').is_visible());page.click('#closeDiagnostics');page.goto('http://127.0.0.1:8774');wait(page,"() => S.job?.status==='success'");check('replay_loaded',page.inner_text('#runMode')=='Recorded replay — no live inference');check('replay_no_models',page.request.get('http://127.0.0.1:8774/health').json()['inference_modules_loaded']==[]);report=page.request.get('http://127.0.0.1:8774/analytics/summary.json').json();check('current_analytics',report.get('matched_candidate',{}).get('local',{}).get('total')==16);check('no_browser_errors',not errors);checks['errors']=errors;checks['budget_before']=before;checks['budget_after']=Ledger().summary();write_json(O/'ui-smoke.json',checks);print(json.dumps(checks,indent=2));browser.close()
