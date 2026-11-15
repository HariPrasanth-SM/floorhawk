"""Normal visitor candidate smoke. No verification-session admission bypass."""
import sys,os,time,json,re,io
if '--event' in sys.argv:
 from event_browser import main
 main()
 raise SystemExit
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));W=ROOT.parent/'floorhawk-modal';U=os.environ.get('FLOORHAWK_TEST_URL','https://sm-hariprasanth--web-ui-candidate.us-east.modal.run');O=W/'verification/ui-release';O.mkdir(parents=True,exist_ok=True)
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
report={'passed':False,'url':U,'jobs':[]};errors=[];posts=[];transient=[True]
def wait(page,expr,timeout=300):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if page.evaluate(expr):return
  page.wait_for_timeout(200)
 raise AssertionError(expr+' status='+page.inner_text('#status'))
def choose(page,fmt,ident,qid):
 page.click('#preloadedTab');page.select_option('#galleryFormat',fmt);page.select_option('#galleryDrawing',ident);wait(page,"() => S.validated===true && S.file?.name==="+json.dumps({'PNG':'plan.png','PDF':'rooms.pdf','IFC':'rooms.ifc'}[fmt]));page.select_option('#galleryQuestion',qid);assert 'Drawing ready'in page.inner_text('#fileName');assert page.evaluate('!!S.image');assert not page.locator('#answerPanel').is_visible()
try:
 with sync_playwright()as p:
  b=p.chromium.launch(headless=True);c=b.new_context(viewport={'width':1366,'height':768});page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:posts.append(r.post_data)if r.method=='POST'and r.url.endswith('/api/jobs')else None)
  page.goto(U);assert page.locator('input[name=code]').is_visible();page.fill('input[name=code]',(W/'.secrets/event-access-code').read_text());page.click('button');wait(page,"() => typeof S!=='undefined' && !!S.config",40);report['normal_login']=True;assert not page.locator('#geminiControl').is_visible();assert not page.locator('.mode-control').is_visible()
  def disrupt(route):
   if transient[0]and re.search(r'/api/jobs/[0-9a-f]{32}$',route.request.url):transient[0]=False;route.fulfill(status=503,content_type='application/json',body='{"error":"Transient smoke-test polling interruption"}')
   else:route.continue_()
  page.route('**/api/jobs/*',disrupt)
  cases=[('PNG','cubi-demo','windows'),('PNG','cubi-demo','doors'),('PDF','rooms-pdf','area-kitchen'),('IFC','rooms-ifc','windows')]
  for i,case in enumerate(cases):
   before=len(posts);choose(page,*case)
   if case[0]=='PDF':
    assert page.locator('#expectedReference').is_visible();text=page.input_value('#question');page.fill('#question',text+' edited');assert not page.locator('#expectedReference').is_visible();page.fill('#question',text)
   page.click('#run');wait(page,'() => S.busy');assert not page.locator('#answerPanel').is_visible()
   if i==0:
    page.select_option('#galleryFormat','PDF');page.select_option('#galleryDrawing','rooms-pdf');wait(page,"() => S.validated && S.file?.name==='rooms.pdf'");wait(page,'() => !S.busy');assert page.evaluate('!S.job');report['pending_selection_isolation']=True;ident=re.search(r'job=([0-9a-f]+)',page.url).group(1);page.goto(U+'/?job='+ident)
   elif i==1:
    page.wait_for_timeout(800);page.reload()
   wait(page,"() => !!S.job?.prediction?.paired && !S.busy",300);job=page.evaluate('S.job');h=job['prediction']['paired']['hybrid'];assert h['status']=='success',h;assert h['provider_attempts']<=2;assert page.inner_text('#answerSource')=='Result';assert job['question']=={'windows':'How many windows are shown on this floor plan?'if case[0]=='PNG'else'How many windows are in this IFC model?','doors':'How many doors are shown on this floor plan?','area-kitchen':'What is the net floor area of room 1.01 in m²?'}[case[2]];assert len(posts)==before+1;assert not page.locator('#pairedAnswers').is_visible();report['jobs'].append({'id':job['id'],'format':case[0],'suggestion':case[2],'answer':h['answer'],'status':h['status'],'attempts':h['provider_attempts'],'local':job['prediction']['paired']['local'].get('answer'),'expected_reference':job.get('expected_reference')});(O/('job-'+str(i)+'.json')).write_text(json.dumps(job,indent=2))
   if case[0]=='PDF':assert h['answer']==12;assert job['expected_reference']['value']==12
   if case[0]=='IFC':assert h['answer']==3;page.wait_for_timeout(3100);assert page.locator('#annotatedExport').is_disabled();report['ifc_placeholder']=True
   else:
    r=page.request.get(U+'/api/jobs/'+job['id']+'/annotated.png?page=1');assert r.ok;from PIL import Image
    im=Image.open(io.BytesIO(r.body()));assert max(im.size)<=4096;assert im.height>0;report[case[0]+'_export_size']=list(im.size)
   for w,hh in [(1366,768),(1920,1080)]:
    page.set_viewport_size({'width':w,'height':hh});assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
  assert not transient[0];report['poll_retry_no_resubmit']=True;report['reload_no_resubmit']=True;assert not errors;report['browser_errors']=errors;report['passed']=True;b.close()
finally:(O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
