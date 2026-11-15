"""Saved-results-only UI verification; no inference or provider dispatch."""
import os,time,json,io,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,write_json
from runtime_paths import RESULTS_ROOT
from v2.budget import Ledger
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
before=Ledger().summary();checks={};errors=[]
def wait(page,expr):
 end=time.monotonic()+30
 while time.monotonic()<end:
  if page.evaluate(expr):return
  page.wait_for_timeout(100)
 raise AssertionError(expr)
with sync_playwright()as p:
 b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1366,'height':768});page.on('pageerror',lambda e:errors.append(str(e)))
 for ident,label in [('7f876a249612426180bc926548d8df1d','windows'),('ec2bf4691f6845dfa39d3d546a9772cb','stoves')]:
  page.goto('http://127.0.0.1:8778/?job='+ident);wait(page,"() => !!S.job && S.boxes.length>0 && !!S.activeEvidence");checks[label+'_answer']=page.inner_text('#modelCount');assert '4'in checks[label+'_answer'];assert page.inner_text('#answerSource')=='Hybrid review';checks[label+'_boxes']=page.evaluate('S.boxes.length');checks[label+'_caption']=page.inner_text('#cropCaption')
  if label=='stoves':assert page.evaluate('S.boxes[0].context_only===true');assert 'no per-object'in checks[label+'_caption']
  else:assert checks[label+'_boxes']==4
  wait(page,"() => !document.getElementById('highResCrop').hidden");assert not page.is_visible('#diagnosticsButton');assert not page.is_visible('#evaluationTab');assert not page.is_visible('#sampleSelect');assert not page.is_visible('.review-bottom');assert page.title().startswith('FloorHAWK');assert page.inner_text('#workspaceTab')=='Explore'
  for w,h in [(1366,768),(1920,1080)]:
   page.set_viewport_size({'width':w,'height':h});assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
  page.check('#showLocalAnswer');wait(page,"() => S.presentationKey.endsWith('|local')");page.uncheck('#showLocalAnswer');wait(page,"() => S.presentationKey.endsWith('|hybrid')");
  response=page.request.get('http://127.0.0.1:8778'+page.get_attribute('#exportDiagnostic','href'));assert response.ok;assert 'floorhawk-'in response.headers['content-disposition'];z=zipfile.ZipFile(io.BytesIO(response.body()));meta=json.loads(z.read('diagnostic.json'));assert meta['query'];assert 'paired'in meta['original_prediction'];assert 'local_evidence_catalog'in meta;checks[label+'_archive']=z.namelist()
 assert Ledger().summary()==before;assert not errors;checks['no_provider_calls']=True;checks['errors']=errors;write_json(RESULTS_ROOT/'floorhawk-ui/verification.json',checks);print(json.dumps(checks,indent=2));b.close()
