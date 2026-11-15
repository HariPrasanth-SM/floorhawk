import os,json,time,traceback
from pathlib import Path
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(Path(__file__).resolve().parents[2]/'cache/playwright')
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];W=R.parent/'floorhawk-modal';O=W/'verification/presenter-browser-finish';O.mkdir(exist_ok=True);U='https://sm-hariprasanth--presenter.us-east.modal.run';out={'passed':False,'checks':[],'runs':[]};errors=[];posts=[]
def check(value,label):
 out['checks'].append({'check':label,'passed':bool(value)})
 assert value,label
def wait(page,expr):
 end=time.monotonic()+90
 while time.monotonic()<end:
  if page.evaluate(expr):return
  page.wait_for_timeout(150)
 raise AssertionError(expr+' / '+page.inner_text('#status'))
def tabs(page,mode):
 check(page.locator('nav button.active').count()==1,'exactly one active tab')
 check(page.locator('#'+('workspaceTab'if mode=='live'else'preloadedTab')).get_attribute('aria-selected')=='true','tab matches '+mode)
def ask(page,q,ref):
 page.fill('#question',q);check(page.locator('#expectedReference').is_hidden(),'upload/custom has no reference');start=time.monotonic();before=len(posts);page.click('#run');wait(page,"() => !S.busy && !!S.job?.prediction && S.job.status==='success'");j=page.evaluate('S.job');answer=page.inner_text('#modelCount');check(len(posts)==before+1,'one UI submission');check(j['question']==q,'answer matches submitted question');check(page.evaluate('S.image && S.image.width>0'),'drawing image rendered');check(page.locator('#evidenceTable').inner_text().strip()!='','evidence list populated');check(page.locator('#answerPanel').is_visible(),'Result visible');out['runs'].append({'question':q,'reference':ref,'answer':answer,'seconds':time.monotonic()-start,'job':j['id'],'source':j['source_name'],'resident':j.get('resident')});return j
try:
 with sync_playwright()as p:
  b=p.chromium.launch(headless=True);c=b.new_context(accept_downloads=True,viewport={'width':1366,'height':768});page=c.new_page();page.set_default_navigation_timeout(90000);page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:posts.append(r.url)if r.method=='POST'and r.url.endswith('/api/jobs')else None)
  page.goto(U);page.fill('input[name=code]',(W/'.secrets/presenter-access-code').read_text());page.click('button');wait(page,"() => typeof S!=='undefined' && !!S.config");tabs(page,'live');check(page.inner_text('#workspaceTab')=='Live Image'and page.inner_text('#preloadedTab')=='Preloaded samples','exact tab labels')
  page.click('#preloadedTab');tabs(page,'samples');page.select_option('#galleryFormat','PNG');page.select_option('#galleryDrawing','png-a');wait(page,"() => S.validated && S.file?.name==='png-a.png'");page.select_option('#galleryQuestion','q2');check(page.locator('#expectedReference').is_visible(),'curated reference visible');page.click('#run');wait(page,"() => !S.busy && !!S.job?.prediction");check(page.inner_text('#modelCount')=='2 count','curated window answer');ident=page.evaluate('S.job.id');n=len(posts);page.reload();wait(page,"() => !!S.job?.prediction && document.querySelector('#expectedReference').hidden===false");check(len(posts)==n,'reload creates no inference');check(page.inner_text('#expectedReferenceValue')=='2 count','restored full reference');check(page.inner_text('#modelCount')=='2 count','restored answer');tabs(page,'samples');page.goto(U+'/?job='+ident);wait(page,"() => !!S.job?.prediction && !document.querySelector('#expectedReference').hidden");check(len(posts)==n,'URL reopening creates no inference');page.fill('#question','A custom question');check(page.locator('#expectedReference').is_hidden(),'edit clears reference immediately')
  page.click('#workspaceTab');tabs(page,'live');page.set_input_files('#upload',str(W/'recording-assets/png-a.png'));wait(page,"() => S.validated && S.file?.name==='png-a.png'");check(page.evaluate('!!S.image && !S.job'),'PNG immediate preview before inference');check(page.locator('#expectedReference').is_hidden(),'new upload clears reference')
  manifest=json.loads((W/'presenter-gallery-manifest.json').read_text())
  for q in manifest[0]['suggestions']:ask(page,q['question'],q['reference'])
  with page.expect_download()as dl:page.click('#annotatedExport')
  dl.value.save_as(O/'png-annotated.png');check((O/'png-annotated.png').stat().st_size>1000,'PNG annotated export downloaded')
  page.set_input_files('#upload',str(W/'recording-assets/pdf-a.pdf'));wait(page,"() => S.validated && S.file?.name==='pdf-a.pdf'");check(page.evaluate('!!S.image && !S.job'),'PDF preview replaces PNG and clears result');check(page.locator('#expectedReference').is_hidden(),'PDF replacement clears reference');tabs(page,'live')
  for q in manifest[2]['suggestions']:ask(page,q['question'],q['reference'])
  wait(page,"() => S.boxes.length>0");check(page.evaluate('S.boxes.length>0'),'PDF localized evidence boxes');page.click('#evidenceNext');page.wait_for_timeout(800);check(page.locator('#cropCaption').inner_text().strip()!='','evidence crop caption');
  with page.expect_download()as dl:page.click('#annotatedExport')
  dl.value.save_as(O/'pdf-annotated.png');check((O/'pdf-annotated.png').stat().st_size>1000,'PDF annotated export downloaded')
  n=len(posts);page.reload();wait(page,"() => !!S.job?.prediction");check(len(posts)==n,'uploaded PDF reload creates no inference');tabs(page,'live');check(page.locator('#expectedReference').is_hidden(),'upload reload no curated reference')
  for ww,hh in[(1366,768),(1920,1080)]:
   page.set_viewport_size({'width':ww,'height':hh});page.wait_for_timeout(300);check(page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'),'no page overflow '+str((ww,hh)));page.screenshot(path=str(O/f'layout-{ww}.png'))
  check(not errors,'no browser console runtime errors');out.update(passed=True,errors=errors,submission_count=len(posts));b.close()
except Exception as e:out['error']=str(e);out['traceback']=traceback.format_exc();print(out['traceback'])
finally:(O/'browser-results.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k not in['runs','traceback']}));print([(x['source'],x['answer'],round(x['seconds'],2))for x in out['runs']])
