"""Real Local-only UI upload/export smoke. No reference or cloud evaluation."""
import os,sys,json,time,io,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,write_json
from runtime_paths import DATASET_ROOT,RESULTS_ROOT
from v2.budget import Ledger
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
def wait(page, expression, timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if page.evaluate(expression):return
  page.wait_for_timeout(150)
 raise AssertionError('Timed out: '+page.inner_text('#status'))
q=json.loads((RESULTS_ROOT/'agile1/experiment/questions.jsonl').read_text().splitlines()[0]);before=Ledger().summary();errors=[];checks={}
with sync_playwright()as p:
 b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1366,'height':768});page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8778');wait(page,'() => S.config?.paired===true');assert not page.is_checked('#geminiToggle')
 page.set_input_files('#upload',str(DATASET_ROOT/q['path']));page.fill('#question',q['question']);page.click('#run');wait(page,"() => !S.busy && S.job?.status==='success'");j=page.evaluate('S.job');checks['actual_local_status']=j['prediction']['status'];checks['job_id']=j['id'];assert j['mode']=='local';assert 'paired'not in j['prediction']
 response=page.request.get('http://127.0.0.1:8778/api/jobs/'+j['id']+'/diagnostic.zip');assert response.ok;z=zipfile.ZipFile(io.BytesIO(response.body()));meta=json.loads(z.read('diagnostic.json'));assert meta['query']==q['question'];assert 'original_prediction'in meta;assert any(n.startswith('source.')for n in z.namelist());checks['diagnostic_members']=z.namelist()
 page.click('#run');wait(page,"() => !S.busy && S.job?.status==='success'");j2=page.evaluate('S.job');checks['second_question_shared_bundle']=j2['prediction']['shared_evidence']['key']==j['prediction']['shared_evidence']['key'];assert checks['second_question_shared_bundle']
 for w,h in [(1366,768),(1920,1080)]:
  page.set_viewport_size({'width':w,'height':h});assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth');checks['viewport_'+str(w)]=True
 page.click('#clearImage');assert page.is_disabled('#run');assert page.evaluate('!S.job');checks['clear_source']=True;checks['no_api_calls']=Ledger().summary()==before;assert checks['no_api_calls'];checks['errors']=errors;assert not errors;write_json(RESULTS_ROOT/'agile1/local-ui-smoke.json',checks);print(json.dumps(checks,indent=2));b.close()
